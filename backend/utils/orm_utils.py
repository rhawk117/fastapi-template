from typing import TYPE_CHECKING, NamedTuple

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import Base

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from sqlalchemy.orm import MappedColumn

    from backend.common.types import SortOrder


class PagedQuery(NamedTuple):
    result: Sequence[Mapping]
    total: int


def get_ordered_statement(
    sort_order: SortOrder, column: str, model: type[Base]
) -> MappedColumn:
    """Returns an ordered SQLAlchemy statement based on the sort order and column."""
    if sort_order == SortOrder.ASC:
        return getattr(model, column).asc()
    elif sort_order == SortOrder.DESC:
        return getattr(model, column).desc()
    else:
        raise ValueError(f'Invalid sort order: {sort_order}')


async def get_one(statement: Select, db: AsyncSession) -> Row | None:
    result = await db.execute(statement)
    return result.one_or_none()


async def get_mappings(statement: Select, db: AsyncSession) -> Sequence[Mapping]:
    result = await db.execute(statement)
    return result.mappings().all()


async def any_exists(statement: Select, db: AsyncSession) -> bool:
    result = await db.execute(statement)
    return result.scalar() is not None


async def get_page(
    offset: int,
    limit: int,
    statement: Select,
    db: AsyncSession,
    model: type[Base],
) -> PagedQuery:
    """Executes a paged query and returns the results along with the total count."""
    paged_statement = statement.offset(offset).limit(limit)

    result = await get_mappings(paged_statement, db)

    count_statement = select(func.count()).select_from(model)
    count_result = await db.execute(count_statement)
    total_count = count_result.scalar_one_or_none()

    return PagedQuery(
        result=result,
        total=total_count if total_count is not None else 0,
    )
