import abc
from enum import StrEnum
from redis import asyncio as aioredis


class RedisRepository:
    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis_client: aioredis.Redis = redis_client
