from sqlalchemy import Case, Enum, String, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from backend import db
from backend.common.models import AuditedMixin, PrimaryKeyId
from backend.core.security.rbac import Role


class User(db.Base, AuditedMixin):
    """Represents a user in the database"""

    __tablename__ = 'users'

    id: Mapped[PrimaryKeyId] = mapped_column()

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    @hybrid_property
    def role_level(self) -> int:  # type: ignore
        return Role.get_role_level(self.role)

    @role_level.expression
    def role_level(cls) -> Case:
        return case(
            (cls.role == Role.READ_ONLY, 1),  # type: ignore
            (cls.role == Role.USER, 2),  # type: ignore
            (cls.role == Role.ADMIN, 3),  # type: ignore
            else_=-1,
        )

    def is_authorized(self, required_role: Role) -> bool:
        return self.role >= required_role

    def __repr__(self) -> str:
        return f'<User(id={self.id} username={self.username} role={self.role})>'


