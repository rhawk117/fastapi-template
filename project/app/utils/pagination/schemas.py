import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Generic, Self, TypeVar

from app.common.schemas import RequestSchema, ResponseSchema
from app.common.types import AlphaString
from pydantic import ConfigDict, Field
from pydantic.types import NonNegativeInt, PositiveInt


class SortOrder(StrEnum):
    ASC = 'asc'
    DESC = 'desc'


def validate_alphanumeric(value: str) -> str:
    if not value.isalnum():
        raise ValueError('Value must be alphanumeric.')
    return value


class PageQueryParams(RequestSchema):
    page_number: Annotated[
        NonNegativeInt,
        Field(..., description='The page number, starting from 0.')
    ]

    size: Annotated[
        PositiveInt,
        Field(
            default=20,
            description='The number of items to return per page.',
            le=100,
        ),
    ]

    @property
    def offset(self) -> int:
        return (self.page_number - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class SortQueryParams(RequestSchema):
    """
    Represents the query parameters for sorting.
    """

    sort_by: Annotated[
        AlphaString | None,
        Field(
            default=None,
            description='The field to sort by, defaults to "id".',
        ),
    ]

    sort_order: Annotated[
        SortOrder,
        Field(
            default=SortOrder.ASC,
            description='The order of sorting, either "asc" or "desc".',
        ),
    ]


class TimeQueryParams(RequestSchema):
    created_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter results created after this date (ISO 8601 format).',
        ),
    ]

    created_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter results created before this date (ISO 8601 format).',
        ),
    ]

    updated_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter results updated after this date (ISO 8601 format).',
        ),
    ]

    updated_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter results updated before this date (ISO 8601 format).',
        ),
    ]


class PageMetadata(ResponseSchema):
    """
    Represents the metadata for paginated responses.
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    page_number: Annotated[
        PositiveInt, Field(..., description='The current page number, starting from 1.')
    ]

    size: Annotated[
        PositiveInt, Field(..., description='The number of items per page.')
    ]

    total_items: Annotated[
        NonNegativeInt,
        Field(..., description='The total number of items across all pages.'),
    ]

    total_pages: Annotated[
        NonNegativeInt,
        Field(
            ...,
            description='The total number of pages based on the total items and size.',
        ),
    ]

    has_previous: Annotated[
        bool, Field(..., description='Whether there is a previous page.')
    ]

    has_next: Annotated[bool, Field(..., description='Whether there is a next page.')]

    previous_page: Annotated[
        NonNegativeInt | None,
        Field(default=None, description='The previous page number, if exists or None.'),
    ]

    next_page: Annotated[
        NonNegativeInt | None,
        Field(default=None, description='The next page number, if it exists or None.'),
    ]

    @classmethod
    def create(cls, *, page: int, size: int, total_items: int) -> Self:
        total_pages = math.ceil(total_items / size) if total_items > 0 else 0

        has_previous = page > 1
        has_next = page < total_pages

        return cls(
            page_number=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_previous=has_previous,
            has_next=has_next,
            previous_page=page - 1 if has_previous else None,
            next_page=page + 1 if has_next else None,
        )


T = TypeVar('T')


class PagedResponse(ResponseSchema, Generic[T]):
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    metadata: Annotated[
        PageMetadata,
        Field(..., description='Metadata about the pagination of the response.'),
    ]

    data: Annotated[
        list[T],
        Field(
            ...,
            description='The list of items returned by the API for the current page.',
        ),
    ]

    @classmethod
    def from_results(
        cls,
        *,
        data: list[T],
        params: PageQueryParams,
        total_items: int,
    ) -> Self:
        metadata = PageMetadata.create(
            page=params.page_number, size=params.size, total_items=total_items
        )
        return cls(metadata=metadata, data=data)
