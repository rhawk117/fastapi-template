

from typing import Annotated

from fastapi import Query

from .models import ColDirection, PageParams, SortOrder

PageNumber = Annotated[
    int,
    Query(
        ge=1,
        description='Page number, starting from 1',
    ),
]
PageSize = Annotated[
    int,
    Query(
        ge=1,
        le=100,
        description='Number of items per page',
    ),
]

async def get_page_params(
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description='Number of items per page',
    ),
    page_number: int = Query(
        default=1,
        ge=1,
        description='Page number, starting from 1',
    ),
) -> PageParams:
    """
    Dependency to get pagination parameters.

    Returns
    -------
    PageParams
        An instance of PageParams with the provided page number and size.
    """
    return PageParams(page_number=page_number, page_size=page_size)

async def get_sort_order(
    direction: ColDirection = Query(
        default='asc',
        description='Sort direction, either "asc" or "desc"',
    ),
) -> SortOrder:
    """
    Dependency to get sorting order.

    Returns
    -------
    SortOrder
        An instance of SortOrder with the specified direction.
    """
    return SortOrder(direction=direction)