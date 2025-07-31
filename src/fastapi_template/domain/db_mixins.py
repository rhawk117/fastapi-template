import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def PrimaryKeyUUID() -> Mapped[str]:
    return mapped_column(
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )


class AuditedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False
    )
