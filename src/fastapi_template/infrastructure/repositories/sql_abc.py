# repositories/base.py
from __future__ import annotations

import uuid
from abc import ABC
from typing import Any, Generic, Mapping, Protocol, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql import Select


class _HasId(Protocol):
    id: uuid.UUID | str | int


_ModelT = TypeVar('_ModelT', bound=_HasId)
_IDT = TypeVar('_IDT')


class SQLModelRepository(Generic[_ModelT, _IDT], ABC):
    """
    generic repository offering common read/write helpers.

    child classes **must** define: `model = MyORMModel`.
    """

    model: type[_ModelT]  # overridden by subclass

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get(
        self, obj_id: _IDT, options: Sequence[Any] | None = None
    ) -> _ModelT | None:
        stmt = select(self.model).where(self.model.id == obj_id)  # type: ignore[no-any-return]
        if options:
            stmt = stmt.options(*options)
        return await self._scalar(stmt)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        filters: Mapping[InstrumentedAttribute, Any] | None = None,
        eager: bool = False,
    ) -> Sequence[_ModelT]:
        stmt: Select[Any] = select(self.model)
        if filters:
            stmt = stmt.filter_by(**{f.key: v for f, v in filters.items()})
        if eager:
            stmt = stmt.options(selectinload('*'))
        stmt = stmt.offset(offset).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def create(self, obj_in: Mapping[str, Any]) -> _ModelT:
        obj = self.model(**obj_in)  # type: ignore[arg-type]
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: _ModelT, obj_in: Mapping[str, Any]) -> _ModelT:
        for k, v in obj_in.items():
            setattr(obj, k, v)
        await self.session.flush()
        return obj

    async def delete(self, obj: _ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def count(self) -> int:
        q = select(func.count()).select_from(self.model)
        return (await self.session.execute(q)).scalar_one()

    async def _scalar(self, stmt: Select[Any]) -> _ModelT | None:
        return (await self.session.execute(stmt)).scalars().first()
