import math
from typing import Annotated, Generic, Self, TypeVar

from pydantic import ConfigDict, Field
from pydantic.types import NonNegativeInt, PositiveInt

from .interface import CustomBaseModel

S = TypeVar('S', bound=CustomBaseModel)


class RequestSchema(CustomBaseModel):
    """
    The base schema and configuration for all request schemas.
    """

    model_config = ConfigDict(
        extra='forbid', strict=True, str_strip_whitespace=True, validate_assignment=True
    )


class ResponseSchema(CustomBaseModel):
    """
    The base schema and configuration for all response schemas.
    """

    pass


class PageParams(RequestSchema):
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


class PageMetadata(ResponseSchema):
    page_number: Annotated[int, PositiveInt, Field(description='Current page number')]

    page_size: Annotated[
        int,
        PositiveInt,
        Field(
            description='Items per page',
        ),
    ]

    total_items: Annotated[
        int,
        NonNegativeInt,
        Field(
            description='Total number of items across all pages',
            ge=0,
            examples=[0, 150, 1000],
        ),
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
        """
        Create a PageMetadata instance with calculated pagination values.
        """
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


class PagedResponse(ResponseSchema, Generic[S]):
    """
    A paginated response schema that includes metadata and a list of items.
    """

    metadata: Annotated[PageMetadata, Field(description='Pagination metadata')]
    data: Annotated[list[S], Field(description='List of items for the current page')]

    @classmethod
    def from_results(
        cls,
        data: list[S],
        page_params: PageParams,
        total_items: int
    ) -> Self:
        metadata = PageMetadata.create(
            page=page_params.page_number,
            size=page_params.size,
            total_items=total_items,
        )
        return cls(metadata=metadata, data=data)
