from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, NamedTuple

from sqlalchemy import ColumnElement, Select, and_, func, select

if TYPE_CHECKING:
    from app.common.models import Base
    from sqlalchemy import ColumnElement
    from sqlalchemy.orm import MappedColumn

    from .schemas import PageQueryParams, SortOrder, SortQueryParams, TimeQueryParams


@dataclasses.dataclass(slots=True)
class QueryConfig:
    db_model: type[Base]
    allowed_sort_fields: set[str] = dataclasses.field(default_factory=set)


def add_sort_query_params(
    statement: Select,
    options: QueryConfig,
    sort_query_params: SortQueryParams,
) -> Select:
    sort_by = sort_query_params.sort_by or 'id'
    sort_order = sort_query_params.sort_order

    if options.allowed_sort_fields and sort_by not in options.allowed_sort_fields:
        raise ValueError(
            f'Sorting by `{sort_by}` is not allowed. '
            f'Allowed fields: {options.allowed_sort_fields}'
        )

    if not hasattr(options.db_model, sort_by):
        raise ValueError(
            f"Column '{sort_by}' does not exist in model '{options.db_model.__name__}'"
        )

    column: MappedColumn = getattr(options.db_model, sort_by)

    if sort_order == SortOrder.ASC:
        statement = statement.order_by(column.asc())
    else:
        statement = statement.order_by(column.desc())

    return statement


def add_time_query_params(
    options: QueryConfig,
    time_query_params: TimeQueryParams,
) -> ColumnElement[bool] | None:
    conditions = []

    if not hasattr(options.db_model, 'created_at') or not hasattr(
        options.db_model, 'updated_at'
    ):
        raise ValueError(
            f"Model '{options.db_model.__name__}' does not have a 'created_at' field."
        )

    if time_query_params.created_after:
        conditions.append(
            options.db_model.created_at >= time_query_params.created_after  # type: ignore
        )
    if time_query_params.created_before:
        conditions.append(
            options.db_model.created_at <= time_query_params.created_before  # type: ignore
        )
    if time_query_params.updated_after:
        conditions.append(
            options.db_model.updated_at >= time_query_params.updated_after  # type: ignore
        )
    if time_query_params.updated_before:
        conditions.append(
            options.db_model.updated_at <= time_query_params.updated_before  # type: ignore
        )

    return and_(*conditions) if conditions else None


def add_pagination_query_params(
    statement: Select,
    page_params: PageQueryParams,
) -> Select:
    return statement.offset(page_params.offset).limit(page_params.limit)


class QueryStatements(NamedTuple):
    query: Select
    count: Select


def create_query_param_statement(
    *,
    options: QueryConfig,
    sort_query_params: SortQueryParams | None = None,
    time_query_params: TimeQueryParams | None = None,
    page_params: PageQueryParams | None = None
) -> QueryStatements:
    base_statement = select(options.db_model)
    count_statement = select(func.count()).select_from(options.db_model)

    if sort_query_params:
        base_statement = add_sort_query_params(
            base_statement, options, sort_query_params
        )

    if time_query_params:
        time_predicate = add_time_query_params(options, time_query_params)
        if time_predicate is not None:
            base_statement = base_statement.where(time_predicate)
            count_statement = count_statement.where(time_predicate)

    if page_params:
        base_statement = add_pagination_query_params(base_statement, page_params)

    return QueryStatements(
        query=base_statement,
        count=count_statement
    )


