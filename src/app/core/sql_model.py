import uuid

from sqlalchemy import MetaData, Uuid, inspect
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

db_meta = MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_N_label)s',
        'uq': '%(table_name)s_%(column_0_N_name)s_key',
        'ck': '%(table_name)s_%(constraint_name)s_check',
        'fk': '%(table_name)s_%(column_0_N_name)s_fkey',
        'pk': '%(table_name)s_pkey',
    }
)


class MappedModel(DeclarativeBase, AsyncAttrs):
    __abstract__ = True
    metadata = db_meta


def _create_record_id() -> uuid.UUID:
    return uuid.uuid4()


class RecordModel(MappedModel):
    """
    Represents a database record with a unique identifier.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=_create_record_id
    )

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, self.__class__) and self.id == __value.id

    def __hash__(self) -> int:
        return self.id.int

    def __repr__(self) -> str:
        inspected = inspect(self)
        if inspected.identity is not None:
            record_id = inspected.identity[0]
            return f'{self.__class__.__name__}(id={record_id!r})'
        return f'{self.__class__.__name__}(id=None)'

    @classmethod
    def generate_id(cls) -> uuid.UUID:
        return _create_record_id()
