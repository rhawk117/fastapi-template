from abc import ABC

import redis.asyncio


class RedisRepository(ABC):
    def __init__(self, redis_client: redis.asyncio.Redis) -> None:
        self.redis_client: redis.asyncio.Redis = redis_client
