import secrets
from dataclasses import dataclass, field
from typing import Final, NamedTuple
from urllib.parse import quote_plus

import redis.asyncio as aioredis
from redis import AuthenticationError

from app.core import settings


class PingResult(NamedTuple):
    success: bool
    exception: Exception | None
    message: str | None = None


@dataclass(slots=True)
class RedisClientOptions:
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    decode_responses: bool = True
    max_connections: int = 10
    retry_on_timeout: bool = True


def create_redis_url(
    *,
    host: str,
    port: int,
    db: int,
    username: str | None = None,
    password: str | None = None,
    ssl: bool = False,
) -> str:
    scheme = 'rediss' if ssl else 'redis'

    auth_part = ''
    if username and password:
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        auth_part = f'{encoded_username}:{encoded_password}@'

    elif password:
        encoded_password = quote_plus(password)
        auth_part = f':{encoded_password}@'

    url = f'{scheme}://{auth_part}{host}:{port}/{db}'

    return url


@dataclass(slots=True)
class AsyncRedisAdapter:
    pool: aioredis.ConnectionPool
    url: str
    _connections: dict[str, aioredis.Redis] = field(default_factory=dict, init=False)

    def register(self, client_id: str, **overrides) -> None:
        if client_id in self._connections:
            return

        self._connections[client_id] = aioredis.Redis(
            connection_pool=self.pool, **overrides
        )

    def get_client(self, client_id: str) -> aioredis.Redis | None:
        return self._connections.get(client_id)

    async def disconnect_client(self, client_id: str) -> None:
        if client := self._connections.pop(client_id, None):
            await client.aclose()

    async def disconnect_all(self) -> None:
        for ids in self._connections.keys():
            await self.disconnect_client(ids)

        self._connections.clear()

    def has(self, client_id: str) -> bool:
        return client_id in self._connections


def create_redis_adapter(
    options: RedisClientOptions | None = None,
) -> AsyncRedisAdapter:
    options = options or RedisClientOptions()
    redis_config = settings.get_app_settings().redis
    url = create_redis_url(
        host=redis_config.HOST,
        port=redis_config.PORT,
        db=redis_config.DB,
        username=redis_config.USERNAME,
        password=redis_config.PASSWORD,
        ssl=redis_config.SSL,
    )
    return AsyncRedisAdapter(
        url=url,
        pool=aioredis.ConnectionPool.from_url(
            url=url,
            decode_responses=options.decode_responses,
            max_connections=options.max_connections,
            socket_timeout=options.socket_timeout,
            socket_connect_timeout=options.socket_connect_timeout,
            health_check_interval=options.health_check_interval,
            retry_on_timeout=options.retry_on_timeout,
        ),
    )


_redis_adapter: Final[AsyncRedisAdapter] = create_redis_adapter()


def make_cid() -> str:
    return secrets.token_urlsafe(8)


async def try_ping_client() -> PingResult:
    client_id = make_cid()
    _redis_adapter.register(client_id)
    try:
        await _redis_adapter.get_client(client_id).ping()  # type: ignore
    except TimeoutError as e:
        return PingResult(
            success=False,
            exception=e,
            message='Timeout while trying to connect to Redis, ensure Redis is reachable',
        )
    except AuthenticationError as e:
        return PingResult(
            success=False,
            exception=e,
            message='Authentication error, please check your Redis credentials',
        )
    except Exception as e:
        return PingResult(
            success=False,
            exception=e,
            message='An unexpected error occurred while trying to connect to Redis',
        )
    finally:
        await _redis_adapter.disconnect_client(client_id)

    return PingResult(
        success=True, exception=None, message='Successfully connected to Redis'
    )


async def connect_redis() -> None:
    """
    Attempts to connect to the Redis server by sending a PING command.

    Raises
    ------
    ConnectionError
        If the connection to Redis fails or if authentication fails.
    """
    ping_result = await try_ping_client()
    if not ping_result.success:
        raise ConnectionError(
            f'Failed to connect to Redis ({ping_result.exception.__class__.__name__})'
            f'due to: {ping_result.exception}. Message: {ping_result.message}'
        ) from ping_result.exception


async def disconnect_redis() -> None:
    """
    Disconnects all Redis clients and closes the connection pool.
    """
    await _redis_adapter.disconnect_all()
    await _redis_adapter.pool.disconnect()


async def get_redis_client():
    '''
    Provides a Redis client instance from the adapter.
    '''
    client_id = make_cid()
    _redis_adapter.register(client_id)
    client: aioredis.Redis = _redis_adapter.get_client(client_id)  # type: ignore
    try:
        yield client
    finally:
        await client.aclose()


def get_adapter() -> AsyncRedisAdapter:
    return _redis_adapter
