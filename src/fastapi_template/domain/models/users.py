from sqlalchemy.orm import Mapped

from fastapi_template.domain.db_mixins import AuditedMixin, PrimaryKeyUUID
from fastapi_template.infrastructure import db


class Users(db.MappedBase, AuditedMixin):
    id: Mapped[str] = PrimaryKeyUUID()

    