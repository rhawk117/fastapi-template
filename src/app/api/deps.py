from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import db, redis_client

from .params.deps import PageParams, SortOrder, get_page_params, get_sort_order

DatabaseDep = Annotated[AsyncSession, Depends(db.get_db)]
RedisDep = Annotated[aioredis.Redis, Depends(redis_client.get_redis_client)]

PaginatedDep = Annotated[
    PageParams,
    Depends(get_page_params),
]

SortOrderDep = Annotated[
    SortOrder,
    Depends(get_sort_order),
]