from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy import ColumnElement, Select
    from sqlalchemy.orm import InstrumentedAttribute

    from backend.common.models import AuditedMixin

    from ..common.schemas.query_params import (
        PageParams,
        SortOrderParams,
        SortType,
        TimeStampParams,
    )


def add_pagination_params(statement: Select, params: PageParams) -> Select:
    return statement.offset(params.offset).limit(params.limit)


def get_timestamp_clauses(
    params: TimeStampParams,
    model: type[AuditedMixin],
) -> Sequence[ColumnElement[bool]]:
    where_clauses = []
    if params.created_before:
        where_clauses.append(model.created_at < params.created_before)

    if params.created_after:
        where_clauses.append(model.created_at > params.created_after)

    if params.updated_before:
        where_clauses.append(model.updated_at < params.updated_before)

    if params.updated_after:
        where_clauses.append(model.updated_at > params.updated_after)

    return where_clauses


def get_sort_clauses(
    sort_order: SortOrderParams,
    columns: Sequence[ColumnElement | InstrumentedAttribute],
) -> Sequence[ColumnElement]:
    if sort_order.sort_order == SortType.asc:
        return [column.asc() for column in columns]
    elif sort_order.sort_order == SortType.desc:
        return [column.desc() for column in columns]
    else:
        raise ValueError(f'Invalid sort order: {sort_order.sort_order}')
