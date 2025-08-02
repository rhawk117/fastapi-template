import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class PkUUIDMixin:
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True,
        unique=True,
        default=lambda: str(uuid.uuid4()),
    )


class PkIntIdMixin:
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
        unique=True,
    )


def now() -> datetime:
    return datetime.now(timezone.utc)


class AuditedMixin:
    created_at: Mapped[datetime] = mapped_column(
        String(50), nullable=False, default=now
    )
    updated_at: Mapped[str] = mapped_column(
        String(50), nullable=False, default=now, onupdate=now
    )
