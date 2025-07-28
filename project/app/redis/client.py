import dataclasses
import logging

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from .config import redis_client_options, redis_config

logger = logging.getLogger(__name__)


def create_redis_client() -> Redis:
    connection_args = dataclasses.asdict(redis_client_options)

    logger.info(f'Creating Redis client with options: {connection_args}')

    redis_client = Redis(
        host=redis_config.REDIS_HOST,
        port=redis_config.REDIS_PORT,
        db=redis_config.REDIS_DB,
        password=redis_config.REDIS_PASSWORD,
        decode_responses=True,
        **connection_args,
    )

    return redis_client


redis_client: Redis = create_redis_client()


async def connect_redis() -> None:
    try:
        await redis_client.ping()
    except TimeoutError as e:
        logger.error(f'Redis connection timed out: {e}')
        raise RuntimeError('Failed to connect to Redis due to timeout.')
    except ConnectionError as e:
        logger.error(f'Redis connection error: {e}')
        raise RuntimeError('Failed to connect to Redis due to connection error.')


async def disconnect_redis() -> None:
    try:
        await redis_client.close()
        logger.info('Redis client disconnected successfully.')
    except Exception as e:
        logger.error(f'Error while disconnecting Redis client: {e}')
        raise RuntimeError('Failed to disconnect from Redis.') from e


async def get_redis_client() -> Redis:
    '''
    Dependency wrapper around the Redis client.

    Returns
    -------
    Redis
    '''
    return redis_client
