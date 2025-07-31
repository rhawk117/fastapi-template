from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from . import const
from .base import MappedBase

if TYPE_CHECKING:
    from fastapi_template.core.settings import SecretSettings, SQLAlchemyOptions


def _create_sqlalchemy_engine(
    options: SQLAlchemyOptions, secrets: SecretSettings
) -> AsyncEngine:
    return create_async_engine(
        url=secrets.DATABASE_URL,
        connection_args=const.CONNECT_ARGS,
        **options.model_dump(exclude_none=True),
    )


def _create_session_maker(async_engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        auto_commit=False
    )


async def _set_sqlite3_pragmas(connection: AsyncConnection) -> None:
    for pragma, value in const.SQLITE3_PRAGMAS.items():
        await connection.execute(text(f'PRAGMA {pragma} = {value}'))


async def _begin_connection(async_engine: AsyncEngine) -> None:
    async with async_engine.begin() as conn:
        await _set_sqlite3_pragmas(conn)

        from fastapi_template.domains import models  # noqa: F401, I001

        await conn.run_sync(MappedBase.metadata.create_all)


class DatabaseConnection:
    _engine: AsyncEngine | None = None
    _AsyncSessionLocal: async_sessionmaker | None = None

    @classmethod
    async def connect(
        cls, *, options: SQLAlchemyOptions, secrets: SecretSettings
    ) -> None:
        if cls._engine:
            raise RuntimeError('Database engine is already connected.')

        cls._engine = _create_sqlalchemy_engine(options, secrets)
        cls._AsyncSessionLocal = _create_session_maker(cls._engine)
        await _begin_connection(cls._engine)

    @classmethod
    async def disconnect(cls) -> None:
        if not cls._engine:
            raise RuntimeError('Database engine is not connected, cannot disconnect.')

        try:
            await cls._engine.dispose()
        except Exception as e:
            raise RuntimeError('Failed to disconnect from the database') from e
        finally:
            cls._engine = None
            cls._session_maker = None

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncConnection, None]:
        async with cls._AsyncSessionLocal() as session:  # type: ignore
            yield session
