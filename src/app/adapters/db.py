import contextlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import sqlparse
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core import path_utils, settings
from app.core.sql_model import MappedModel

AsyncSessionMaker = async_sessionmaker[AsyncSession]
logger = logging.getLogger(__name__)

@dataclass(slots=True)
class AsyncEngineOptions:
    pool_size: int = 10
    pool_timeout: int = 30
    pool_size: int = 10
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_use_lifo: bool = True


@dataclass(slots=True)
class AsyncSessionOptions:
    expire_on_commit: bool = False
    autoflush: bool = False


@dataclass(slots=True)
class SqlalchemyAdapter:
    engine: AsyncEngine
    async_session_maker: AsyncSessionMaker
    url: URL

    def make_db_dir(self):
        db_settings = settings.get_app_settings().db
        if db_settings.DIRECTORY:
            db_dir = path_utils.abs_root_path(db_settings.DIRECTORY)
            db_dir.mkdir(parents=True, exist_ok=True)

    @contextlib.asynccontextmanager
    async def connection(self):
        try:
            async with self.engine.connect() as conn:
                yield conn
        except Exception as e:
            logger.error(f'Error during engine connection: {e}')



def create_sqlalchemy_adapter(
    *,
    connect_args: dict | None = None,
    engine_options: AsyncEngineOptions | None = None,
    session_options: AsyncSessionOptions | None = None,
) -> SqlalchemyAdapter:
    engine_options = engine_options or AsyncEngineOptions()
    session_options = session_options or AsyncSessionOptions()

    config = settings.get_app_settings()

    url = URL.create(
        drivername=config.db.DRIVER_NAME,
        database=config.db.database,
    )
    engine = create_async_engine(
        url=url,
        echo=config.db.ECHO,
        connect_args=connect_args or {},
        pool_size=engine_options.pool_size,
        pool_timeout=engine_options.pool_timeout,
        max_overflow=engine_options.max_overflow,
        pool_pre_ping=engine_options.pool_pre_ping,
        pool_use_lifo=engine_options.pool_use_lifo,
    )

    async_session_maker = AsyncSessionMaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=session_options.expire_on_commit,
        autoflush=session_options.autoflush,
    )

    return SqlalchemyAdapter(
        engine=engine,
        async_session_maker=async_session_maker,
        url=url,
    )

_sqlalchemy_adapter: Final[SqlalchemyAdapter] = create_sqlalchemy_adapter(
    connect_args={
        'check_same_thread': False,
    }
)

async def register_models(conn: AsyncConnection) -> None:
    """
    Register all models with the database connection.

    This function should be called after the database connection is established.
    """
    await conn.run_sync(MappedModel.metadata.create_all)


async def set_sqlite_pragmas(conn: AsyncConnection) -> None:
    db_config = settings.get_app_settings().db

    for pragma, value in db_config.pragmas.items():
        statement = text(f'PRAGMA {pragma}={value};')
        await conn.execute(statement)



async def connect_db() -> None:
    """Connects to the database and creates tables if they do not exist."""
    _sqlalchemy_adapter.make_db_dir()

    async with _sqlalchemy_adapter.connection() as conn:
        await set_sqlite_pragmas(conn)
        await register_models(conn)


async def disconnect_db() -> None:
    """Disconnects from the database."""
    logger.info('Disconnecting from database.')
    await _sqlalchemy_adapter.engine.dispose()


async def run_sql_file(sql_path: Path) -> None:
    """
    Executes the SQL statements from the provided sql file.

    Parameters
    ----------
    sql_path : Path
        The path to the SQL seed file.
    """
    if not sql_path.exists() or not sql_path.is_file():
        logger.warning(f'Seed file {sql_path} does not exist or is not a file.')
        return
    raw_sql = sql_path.read_text()
    statements = [stmt.strip() for stmt in sqlparse.split(raw_sql) if stmt.strip()]
    async with _sqlalchemy_adapter.connection() as conn:
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                logger.error(f'Error executing statement: {stmt}\nError: {e}')
                raise

def get_adapter() -> SqlalchemyAdapter:
    return _sqlalchemy_adapter

async def get_db():
    async with _sqlalchemy_adapter.async_session_maker() as session:
        yield session