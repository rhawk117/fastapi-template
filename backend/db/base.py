from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class MappedBase(AsyncAttrs, DeclarativeBase):
    """base model all database models must inherit from"""


class Base(MappedBase):
    """base model all database models must inherit from"""

    __abstract__ = True
