import dataclasses
import logging
import os
from collections.abc import AsyncGenerator

from app.common.models import MappedBase
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import database_config, engine_options
from .const import CONNECT_ARGS, DRIVER_NAME, SQLITE_PRAGMAS

logger = logging.getLogger(__name__)


def create_orm_engine() -> AsyncEngine:
    database_url = URL.create(
        drivername=DRIVER_NAME,
        database=database_config.database,
    )
    engine_options_kwargs = dataclasses.asdict(engine_options)
    logger.debug(f'Database URL:  {database_url}')
    return create_async_engine(
        url=database_url,
        echo=database_config.SQLALCHEMY_ECHO,
        connect_args=CONNECT_ARGS,
        **engine_options_kwargs,
    )


async_engine = create_orm_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def set_sqlite_pragmas(connection: AsyncConnection) -> None:
    logger.debug('Setting SQLite pragmas')
    pragmas = SQLITE_PRAGMAS
    for pragma, value in pragmas.items():
        statement = text(f'PRAGMA {pragma} = {value}')
        await connection.execute(statement)

    logger.info('SQLite pragmas set successfully')


async def connect_db() -> None:
    if database_config.DATABASE_FILE_NAME != ':memory:':
        os.makedirs(database_config.DATABASE_DIRECTORY, exist_ok=True)

    logger.debug('Opening database connection')
    async with async_engine.begin() as connection:
        logger.info('Connected to the database successfully')
        await set_sqlite_pragmas(connection)
        from . import models  # noqa: F401, I001

        logger.debug('Creating database tables')
        await connection.run_sync(MappedBase.metadata.create_all)


async def disconnect_db() -> None:
    logger.info('Disconnecting from the database')
    await async_engine.dispose()
    logger.info('Database disconnected successfully')


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
