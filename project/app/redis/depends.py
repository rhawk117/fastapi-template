from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from .client import get_redis_client

RedisDepends = Annotated[Redis, Depends(get_redis_client)]
