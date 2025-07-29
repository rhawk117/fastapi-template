
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session

DatabaseDepends = Annotated[AsyncSession, Depends(get_session)]
