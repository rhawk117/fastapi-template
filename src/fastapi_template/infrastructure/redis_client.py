from __future__ import annotations

from typing import TYPE_CHECKING

import redis.asyncio

if TYPE_CHECKING:
    from fastapi_template.core.settings import RedisClientOptions, SecretSettings


def _create_redis_client(
    options: RedisClientOptions, secrets: SecretSettings
) -> redis.asyncio.Redis:
    connection_params = {
        'host': secrets.REDIS_HOST,
        'port': secrets.REDIS_PORT,
        'db': secrets.REDIS_DB,
        'decode_responses': True,
        **options.model_dump(exclude_none=True),
    }

    if secrets.REDIS_USERNAME and secrets.REDIS_PASSWORD:
        connection_params.update(
            {'username': secrets.REDIS_USERNAME, 'password': secrets.REDIS_PASSWORD}
        )

    return redis.asyncio.Redis(**connection_params)


async def _open_redis_connection(connection: redis.asyncio.Redis) -> None:
    try:
        await connection.ping()
    except redis.ConnectionError as e:
        raise RuntimeError('Failed to connect to Redis') from e
    except redis.TimeoutError as e:
        raise RuntimeError('Redis connection timed out') from e


class RedisClient:
    _connection: redis.asyncio.Redis | None = None

    @classmethod
    async def connect(
        cls, *, options: RedisClientOptions, secrets: SecretSettings
    ) -> None:
        if cls._connection:
            raise RuntimeError('Redis client is already connected.')

        cls._connection = _create_redis_client(options, secrets)
        await _open_redis_connection(cls._connection)

    @classmethod
    async def disconnect(cls) -> None:
        if not cls._connection:
            raise RuntimeError(
                'Redis client is not connected, cannot disconnect client.'
            )
        try:
            await cls._connection.close()
        except redis.ConnectionError as e:
            raise RuntimeError('Failed to disconnect from Redis') from e

    @classmethod
    async def get_client(cls) -> redis.asyncio.Redis:
        if not cls._connection:
            raise RuntimeError('Redis client is not connected.')
        return cls._connection


__all__ = ['RedisClient']
