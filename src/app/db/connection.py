from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .base import MappedBase
from .const import CONNECT_ARGS, SQLITE3_PRAGMAS
from .settings import get_db_settings


def _create_sqlalchemy_engine() -> AsyncEngine:
    db_settings = get_db_settings()

    return create_async_engine(
        url=db_settings.url,
        connection_args=CONNECT_ARGS,
        **db_settings.engine_args,
    )


_async_engine = _create_sqlalchemy_engine()
_AsyncSessionLocal = async_sessionmaker(
    bind=_async_engine, expire_on_commit=False, auto_commit=False
)


async def _set_sqlite3_pragmas(connection: AsyncConnection) -> None:
    for pragma, value in SQLITE3_PRAGMAS.items():
        await connection.execute(text(f'PRAGMA {pragma} = {value}'))


async def connect_db() -> None:
    """
    Connects to the database and initializes the engine.
    """
    if not _async_engine:
        raise RuntimeError('Database engine is not initialized.')

    async with _async_engine.begin() as conn:
        await _set_sqlite3_pragmas(conn)
        from . import _mapped_models  # noqa: F401

        await conn.run_sync(MappedBase.metadata.create_all)


async def disconnect_db() -> None:
    if not _async_engine:
        raise RuntimeError('Database engine is not initialized.')

    try:
        await _async_engine.dispose()
    except Exception as e:
        raise RuntimeError('Failed to disconnect from the database') from e


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async session for a database transaction.
    """
    async with _AsyncSessionLocal() as session:
        yield session
