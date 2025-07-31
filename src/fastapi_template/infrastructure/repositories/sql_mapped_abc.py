# repositories/mapped_repo.py
from __future__ import annotations

from abc import ABC
from collections.abc import AsyncGenerator, Iterable, Mapping, Sequence
from typing import Any, Generic, NamedTuple, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute
from sqlalchemy.sql import ColumnElement, Select

_ModelT = TypeVar('_ModelT', bound=DeclarativeBase)
_IDT = TypeVar('_IDT')

COMPILE_CACHE: dict[str, Any] = {}  # global; tweak with LRU or dogpile.cache


def cols(
    model: type[_ModelT],
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> Sequence[ColumnElement[Any]]:
    """
    Returns a list of columns from the model's table,
    optionally filtered by include/exclude sets.

    Parameters
    ----------
    model : type[_ModelT]
    include : set[str] | None, optional
        _columns to include_, by default None
    exclude : set[str] | None, optional
        _columns to exclude_, by default None

    Returns
    -------
    Sequence[ColumnElement[Any]]
    """
    table = model.__table__
    wanted = table.c.keys()
    if include:
        wanted = [c for c in wanted if c in include]
    if exclude:
        wanted = [c for c in wanted if c not in exclude]
    return [table.c[name] for name in wanted]


def chunked_in(
    col: ColumnElement[Any],
    values: Sequence[Any],
    chunk_size: int = 1000,
) -> ColumnElement[Any]:
    """
    Breaks `col IN (values)` into OR-ed chunks to respect driver limits.

    Parameters
    ----------
    col : ColumnElement[Any]
    values : Iterable[Any]
    chunk_size : int, optional
        _size of chunk_, by default 1000

    Returns
    -------
    ColumnElement[Any]
    """
    chunks = []
    for i in range(0, len(values), chunk_size):
        chunk = values[i : i + chunk_size]
        chunks.append(col.in_(chunk))

    return or_(*chunks)


def to_pydantic(mapping: Mapping[str, Any], *, schema_cls: type[BaseModel]) -> Any:
    return schema_cls.model_validate(mapping)


def to_object(mapping: Mapping[str, Any], *, object_cls: type[object]) -> Any:
    return object_cls(**mapping)


class PageResult(NamedTuple):
    items: list[Mapping[str, Any]]
    total: int
    limit: int
    offset: int

    @property
    def next_offset(self) -> int | None:
        nxt = self.offset + self.limit
        return nxt if nxt < self.total else None


class SQLMappedRepository(Generic[_ModelT, _IDT], ABC):
    """
    SQLAlchemy wrapper to perform highly optimized reads that return
    dictionaries instead of ORM objects.
    """

    model: type[_ModelT]  # override
    _id_attr_name: str = 'id'  # override if PK != "id"

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    def select_columns(
        self,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
    ) -> Select[Any]:
        key = f'{self.model.__name__}:{include}:{exclude}'
        if key in COMPILE_CACHE:
            return COMPILE_CACHE[key]

        stmt = select(*cols(self.model, include, exclude))
        COMPILE_CACHE[key] = stmt
        return stmt

    async def by_id(
        self,
        obj_id: _IDT,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
    ) -> Mapping[str, Any] | None:
        stmt = self.select_columns(include=include, exclude=exclude).where(
            getattr(self.model, self._id_attr_name) == obj_id
        )
        res: Result = await self.session.execute(stmt)
        return res.mappings().first()  # type: ignore[no-any-return]

    async def list(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        where_clauses: Sequence[ColumnElement[Any]] | None = None,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Mapping[str, Any]]:
        stmt = self.select_columns(include=include, exclude=exclude)
        if filters:
            stmt = stmt.filter_by(**filters)

        if where_clauses:
            stmt = stmt.where(*where_clauses)

        stmt = stmt.offset(offset).limit(limit)

        res: Result = await self.session.execute(stmt)
        return res.mappings().all()  # type: ignore[no-any-return]

    async def stream_all(
        self,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        chunk: int = 1000,
    ) -> AsyncGenerator[Mapping[str, Any]]:
        """
        Memory-efficient streaming of all rows in the table uses `yield_per` to
        fetch under the hood

        Parameters
        ----------
        include : set[str] | None, optional
        exclude : set[str] | None, optional
        chunk : int, optional

        Yields
        ------
        Iterator[AsyncGenerator[Mapping[str, Any]]]
            _description_
        """
        stmt = self.select_columns(include=include, exclude=exclude).execution_options(
            yield_per=chunk
        )

        stream = await self.session.stream(stmt)
        async for row in stream.mappings():
            yield row  # type: ignore[no-any-return]

    async def by_ids(
        self,
        ids: Sequence[_IDT],
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
    ) -> list[Mapping[str, Any]]:
        if not ids:
            return []
        stmt = self.select_columns(include=include, exclude=exclude).where(
            chunked_in(getattr(self.model, self._id_attr_name), ids)
        )
        res = await self.session.execute(stmt)
        return res.mappings().all()  # type: ignore[no-any-return]

    async def paginate(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        sort: Iterable[tuple[InstrumentedAttribute, str]] | None = None,
        group_by: Iterable[InstrumentedAttribute] | None = None,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        filters: Mapping[str, Any] | None = None,
        where_clauses: Sequence[ColumnElement[Any]] | None = None,
    ) -> PageResult:
        stmt: Select[Any] = self.select_columns(include=include, exclude=exclude)

        if filters:
            stmt = stmt.filter_by(**filters)

        if group_by:
            stmt = stmt.group_by(*group_by)

        if where_clauses:
            stmt = stmt.where(*where_clauses)

        # uses funnction `count(*) OVER()` so we only need to run one query
        total_col = func.count().over().label('_full_count')
        stmt = stmt.add_columns(total_col)

        if sort:
            order_clauses: list[ColumnElement[Any]] = []
            for col, direction in sort:
                order_clauses.append(
                    col.asc() if direction.lower() == 'asc' else col.desc()
                )
            stmt = stmt.order_by(*order_clauses)

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        total = rows[0]['_full_count'] if rows else 0
        items = [{k: v for k, v in r.items() if k != '_full_count'} for r in rows]

        return PageResult(items=items, total=total, limit=limit, offset=offset)  # type: ignore[no-any-return]
