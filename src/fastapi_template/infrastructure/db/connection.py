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

from fastapi_template.core import settings

from . import const
from .base import MappedBase


def _create_sqlalchemy_engine() -> AsyncEngine:
    secrets = settings.get_secrets()
    options = settings.get_config().sqlalchemy

    return create_async_engine(
        url=secrets.DATABASE_URL,
        connection_args=const.CONNECT_ARGS,
        **options.model_dump(exclude_none=True),
    )


_async_engine = _create_sqlalchemy_engine()
_AsyncSessionLocal = async_sessionmaker(
    bind=_async_engine,
    expire_on_commit=False,
    auto_commit=False
)


async def _set_sqlite3_pragmas(connection: AsyncConnection) -> None:
    for pragma, value in const.SQLITE3_PRAGMAS.items():
        await connection.execute(text(f'PRAGMA {pragma} = {value}'))


async def connect_db() -> None:
    """Connects to the database and initializes the engine."""
    if not _async_engine:
        raise RuntimeError('Database engine is not initialized.')

    async with _async_engine.begin() as conn:
        await _set_sqlite3_pragmas(conn)

        from fastapi_template.domain import models  # noqa: F401, I001

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
    async with _AsyncSessionLocal() as session:
        yield session
