from . import db, redis
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated


DatabaseDepends = Annotated[AsyncSession, Depends(db.get_session)]
RedisDepends = Annotated[aioredis.Redis, Depends(redis.get_redis_client)]
