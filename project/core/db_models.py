from datetime import UTC, datetime
from typing import Annotated

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class MappedBase(AsyncAttrs, DeclarativeBase):
    """base model all database models must inherit from"""


PrimaryKeyId = Annotated[
    int, mapped_column(autoincrement=True, primary_key=True, index=True, unique=True)
]


class AuditedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False,
    )


class DatasourceMixin:
    id: Mapped[PrimaryKeyId] = mapped_column()

    username: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


class Base(MappedBase):
    """base model all database models must inherit from"""

    __abstract__ = True
