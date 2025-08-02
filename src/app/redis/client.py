from __future__ import annotations

from urllib.parse import quote_plus

import redis.asyncio

from app.core.config import settings


def create_redis_url(
    *,
    host: str,
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    database: int = 0,
    ssl: bool = False,
) -> str:
    """
    Create a Redis URL with URL encoding for special characters in credentials.

    This version is safer when usernames/passwords contain special characters.
    """
    scheme = 'rediss' if ssl else 'redis'

    auth_part = ''
    if username and password:
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        auth_part = f'{encoded_username}:{encoded_password}@'
    elif password:
        encoded_password = quote_plus(password)
        auth_part = f':{encoded_password}@'

    url = f'{scheme}://{auth_part}{host}:{port}/{database}'

    return url


class RedisClient:
    def __init__(self) -> None:
        client_options = settings.get_config().redis_client
        secrets = settings.get_secrets()
        self._url = create_redis_url(
            host=secrets.REDIS_HOST,
            port=secrets.REDIS_PORT,
            username=secrets.REDIS_USERNAME,
            password=secrets.REDIS_PASSWORD,
            database=secrets.REDIS_DB,
        )
        self._client = redis.asyncio.from_url(
            self._url,
            decode_responses=True,
            **client_options.model_dump(),
        )

    async def connect(self) -> None:
        try:
            await self._client.ping()
        except redis.ConnectionError as e:
            raise RuntimeError('Failed to connect to Redis') from e
        except redis.TimeoutError as e:
            raise RuntimeError('Redis connection timed out') from e

    async def disconnect(self) -> None:
        try:
            await self._client.close()
        except redis.ConnectionError as e:
            raise RuntimeError('Failed to disconnect from Redis') from e

    async def get_client(self) -> redis.asyncio.Redis:
        """
        Returns the Redis client instance.

        Raises
        ------
        RuntimeError
            If the Redis client is not connected.
        """
        if not self._client:
            raise RuntimeError('Redis client is not connected.')
        return self._client


redis_client = RedisClient()
