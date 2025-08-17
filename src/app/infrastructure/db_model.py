from .db.base import MappedBase


class DBModel(MappedBase):
    __abstract__ = True
