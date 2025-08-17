from datetime import datetime, UTC
from typing import Annotated
from sqlalchemy.orm import mapped_column, Mapped
import uuid


def create_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


PrimaryKeyUUID: Mapped[str] = mapped_column(
    primary_key=True,
    default=create_uuid,
    index=True,
    nullable=False,
)


class AuditedMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
