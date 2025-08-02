from typing import Annotated

import redis.asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domains.users.repository import UserRepository
from app.domains.users.services import UserService
from app.redis.client import redis_client

DatabaseDepends = Annotated[AsyncSession, Depends(get_session)]
RedisDepends = Annotated[redis.asyncio.Redis, Depends(redis_client.get_client)]


async def get_user_repo(db: DatabaseDepends) -> UserRepository:
    return UserRepository(db)


async def get_user_service(db: DatabaseDepends) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


UserRepoDepends = Annotated[UserRepository, Depends(get_user_repo)]
UserServiceDepends = Annotated[UserService, Depends(get_user_service)]
