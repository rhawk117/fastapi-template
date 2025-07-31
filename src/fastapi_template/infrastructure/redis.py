from __future__ import annotations

import redis.asyncio

from fastapi_template.core import settings


def _create_redis_client() -> redis.asyncio.Redis:
    secrets = settings.get_secrets()
    options = settings.get_config().redis_client

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


_redis_client = _create_redis_client()


async def connect_client(connection: redis.asyncio.Redis) -> None:
    try:
        await connection.ping()
    except redis.ConnectionError as e:
        raise RuntimeError('Failed to connect to Redis') from e
    except redis.TimeoutError as e:
        raise RuntimeError('Redis connection timed out') from e


async def disconnect_client(connection: redis.asyncio.Redis) -> None:
    try:
        await connection.close()
    except redis.ConnectionError as e:
        raise RuntimeError('Failed to disconnect from Redis') from e


async def get_redis_client() -> redis.asyncio.Redis:
    """
    Returns the Redis client instance.

    Raises
    ------
    RuntimeError
        If the Redis client is not connected.
    """
    if not _redis_client:
        raise RuntimeError('Redis client is not connected.')
    return _redis_client

