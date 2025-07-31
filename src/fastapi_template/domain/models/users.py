from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_template.domain.db_mixins import AuditedMixin, PrimaryKeyUUID
from fastapi_template.infrastructure import db
from fastapi_template.infrastructure.security.rbac import UserRole


class User(db.MappedBase, AuditedMixin):
    id: Mapped[str] = PrimaryKeyUUID()

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
