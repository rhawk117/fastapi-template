from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class MappedBase(AsyncAttrs, DeclarativeBase):
    """
    Base class for all models in the application.
    It inherits from _MappedBase which provides async capabilities.
    """

    __abstract__ = True
