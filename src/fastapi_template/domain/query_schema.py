import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Generic, Self, TypeVar

from pydantic import Field
from pydantic.types import NonNegativeInt, PositiveInt

from fastapi_template.core.pydantic import CustomBaseModel


class PageParams(CustomBaseModel):
    """
    Generic pagination parameters for API endpoints.

    Designed to be frontend-friendly with sensible defaults and validation.
    """

    page_number: Annotated[
        int,
        PositiveInt,
        Field(
            default=1,
            description='The page number, starts at 1',
            ge=1,
        ),
    ]

    size: Annotated[
        int,
        PositiveInt,
        Field(
            default=20,
            description='Number of items per page',
            ge=1,
            le=100,
        ),
    ]

    @property
    def offset(self) -> int:
        """Calculate database offset from page and size."""
        return (self.page_number - 1) * self.size

    @property
    def limit(self) -> int:
        """Database limit (alias for size for clarity)."""
        return self.size


class TimeStampParams(CustomBaseModel):
    created_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter items created before this date',
        ),
    ] = None

    created_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter items created after this date',
        ),
    ] = None

    updated_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter items updated before this date',
        ),
    ] = None

    updated_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description='Filter items updated after this date',
        ),
    ] = None


class SortType(StrEnum):
    asc = 'asc'
    desc = 'desc'


class SortParams(CustomBaseModel):
    order: Annotated[
        SortType,
        Field(
            default=SortType.asc,
            description='The order to sort the items by (asc or desc)',
        ),
    ]


class PageMetadata(CustomBaseModel):
    page_number: Annotated[int, PositiveInt, Field(description='Current page number')]

    page_size: Annotated[int, PositiveInt, Field(description='Items per page')]

    total_items: Annotated[
        int, NonNegativeInt, Field(description='Total number of items across all pages')
    ]

    total_pages: Annotated[int, PositiveInt, Field(description='Total number of pages')]

    has_previous: Annotated[
        bool,
        Field(description='Whether there is a previous page'),
    ]

    has_next: Annotated[bool, Field(description='Whether there is a next page')]

    previous_page: Annotated[
        int | None,
        Field(
            default=None,
            description='Previous page number (null if no previous page)',
        ),
    ]

    next_page: Annotated[
        int | None,
        Field(
            default=None,
            description='Next page number (null if no next page)',
        ),
    ]

    @classmethod
    def create(
        cls,
        *,
        page: int,
        size: int,
        total_items: int,
    ) -> Self:
        total_pages = math.ceil(total_items / size) if size > 0 else 0
        has_previous = page > 1
        has_next = page < total_pages

        return cls(
            page_number=page,
            page_size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_previous=has_previous,
            has_next=has_next,
            previous_page=page - 1 if has_previous else None,
            next_page=page + 1 if has_next else None,
        )


S = TypeVar('S', bound=CustomBaseModel)


class PagedResponse(CustomBaseModel, Generic[S]):
    """
    A paginated response schema that includes metadata and a list of items.
    """

    metadata: Annotated[PageMetadata, Field(description='Pagination metadata')]
    data: Annotated[list[S], Field(description='List of items for the current page')]

    @classmethod
    def from_results(
        cls, data: list[S], page_params: PageParams, total_items: int
    ) -> Self:
        metadata = PageMetadata.create(
            page=page_params.page_number,
            size=page_params.size,
            total_items=total_items,
        )
        return cls(metadata=metadata, data=data)
