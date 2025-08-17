import logging
from urllib.parse import quote_plus

import redis.asyncio
from redis.exceptions import AuthenticationError, TimeoutError

from .settings import redis_options, redis_secrets

logger = logging.getLogger(__name__)


def _create_redis_url(
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


def _create_redis_client(
    url: str,
    *,
    socket_connect_timeout: float = redis_options.socket_connect_timeout,
    socket_timeout: float = redis_options.socket_timeout,
    max_connections: int = redis_options.max_connections,
    health_check_interval: int = redis_options.health_check_interval,
) -> redis.asyncio.Redis:
    return redis.asyncio.from_url(
        url=url,
        socket_connect_timeout=socket_connect_timeout,
        socket_timeout=socket_timeout,
        max_connections=max_connections,
        health_check_interval=health_check_interval,
    )


URL = _create_redis_url(
    host=redis_secrets.HOST,
    port=redis_secrets.PORT,
    db=redis_secrets.DB,
    username=redis_secrets.USERNAME,
    password=redis_secrets.PASSORD,
)

_redis_client = _create_redis_client(url=URL)


async def ping_redis_client() -> bool:
    logger.debug('Pinging Redis server...')
    success = False
    try:
        await _redis_client.ping()
        success = True
    except TimeoutError as e:
        logger.critical(f'Redis ping failed: {e}')
    except AuthenticationError as e:
        logger.critical(f'Redis authentication failed: {e}')
    logger.debug(f'Redis ping successful: {success}')
    return success


async def get_redis_client() -> redis.asyncio.Redis:
    return _redis_client


async def close_redis_connection() -> None:
    logger.info('Closing Redis connection...')
    await _redis_client.close()
