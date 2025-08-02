from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeAlias, TypeVar

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.base import ExecutableOption

_OrderClause: TypeAlias = tuple[ColumnElement[Any], Literal['asc', 'desc']]


def prepare_select(
    select: Select[Any],
    *,
    where_clauses: Sequence[ColumnElement[bool]] | None = None,
    filters: Mapping[InstrumentedAttribute, Any] | None = None,
    options: Sequence[ExecutableOption] | None = None,
    group_by: Sequence[ColumnElement[Any]] | None = None,
    order_by: Sequence[_OrderClause] | None = None,
) -> Select[Any]:
    """
    Returns a list of predicates from the model's table,
    optionally filtered by include/exclude sets.

    Parameters
    ----------
    model : type[_ModelT]
    include : set[str] | None, optional
        _predicates to include_, by default None
    exclude : set[str] | None, optional
        _predicates to exclude_, by default None

    Returns
    -------
    Sequence[ColumnElement[Any]]
    """
    if where_clauses:
        select = select.where(*where_clauses)

    if filters:
        filtered = {f.key: v for f, v in filters.items()}
        select = select.filter_by(**filtered)

    if options:
        select = select.options(*options)

    if group_by:
        select = select.group_by(*group_by)

    if order_by:
        order_clauses = [
            (clause[0].asc() if clause[1] == 'asc' else clause[0].desc())
            for clause in order_by
        ]
        select = select.order_by(*order_clauses)

    return select


def paginate_select(
    select: Select[Any],
    *,
    limit: int = 100,
    offset: int = 0,
    total_column: str | None = None,
) -> Select[Any]:
    total_col = func.count().over().label(total_column or '_full_count')
    select = select.add_columns(total_col)
    return select.limit(limit).offset(offset)


_ModelT = TypeVar('_ModelT')


async def select_by_id(
    obj_id: Any,
    db: AsyncSession,
    *,
    model: type[_ModelT],
    options: Sequence[Any] | None = None,
) -> _ModelT | None:
    stmt = select(model).where(model.id == obj_id)  # type: ignore[no-any-return]
    if options:
        stmt = stmt.options(*options)
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_by_id(
    obj_id: Any,
    db: AsyncSession,
    *,
    model: type[_ModelT],
    update_args: Mapping[str, Any],
    commit: bool = True,
    refresh: bool = False,
) -> _ModelT | None:
    instance = await select_by_id(obj_id, db, model=model)
    if not instance:
        return None

    for key, value in update_args.items():
        setattr(instance, key, value)
    db.add(instance)

    if commit:
        await db.commit()

    if refresh:
        await db.refresh(instance)

    return instance


async def delete_by_id(
    obj_id: Any,
    db: AsyncSession,
    *,
    model: type[_ModelT],
    commit: bool = True,
) -> bool:
    instance = await select_by_id(obj_id, db, model=model)
    if not instance:
        return False

    await db.delete(instance)

    if commit:
        await db.commit()

    return True


async def count_by(
    db: AsyncSession,
    *,
    model: type[_ModelT],
    filters: Mapping[InstrumentedAttribute, Any] | None = None,
    where: Sequence[Any] | None = None,
) -> int:
    stmt = select(func.count()).select_from(model)
    if filters:
        stmt = stmt.filter_by(**{f.key: v for f, v in filters.items()})
    if where:
        stmt = stmt.where(*where)

    return (await db.execute(stmt)).scalar_one()


async def select_all_by(
    db: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
    model: type[_ModelT],
    filters: Mapping[InstrumentedAttribute, Any] | None = None,
    where: Sequence[Any] | None = None,
) -> Sequence[_ModelT]:
    stmt: Select[Any] = select(model)
    complete_select = prepare_select(stmt, where_clauses=where, filters=filters)

    stmt = complete_select.limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()
