from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domains.mixins import AuditedMixin, PkIntIdMixin, PkUUIDMixin


class Base(DeclarativeBase):
    pass


class Role(Base, AuditedMixin, PkIntIdMixin):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    role_level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # one-to-many
    users: Mapped[list['User']] = relationship('User', back_populates='role')


class User(PkUUIDMixin, AuditedMixin, Base):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    role_id: Mapped[int] = mapped_column(
        ForeignKey('roles.id'),
        nullable=False,
        index=True
    )
    # one-to-many relationship with Role
    role: Mapped['Role'] = relationship('Role', back_populates='users', lazy='selectin')

    __table_args__ = (
        Index('ix_users_active_email', 'is_active', 'email'),
        Index('ix_users_active_username', 'is_active', 'username'),
        Index('ix_users_role_active', 'role_id', 'is_active'),
    )
