




import math
from typing import Annotated, Generic, Self, TypeVar

from pydantic import ConfigDict, Field

from app.core.schema import PydanticSchema


class RequestSchema(PydanticSchema):

    model_config = ConfigDict(
        extra='forbid',
        strict=True,
        str_strip_whitespace=True,
    )

class ResponseSchema(PydanticSchema): ...


class PageTotals(ResponseSchema):
    pages: int = Field(..., description='Total number of pages')
    items: int = Field(..., description='Total number of items across all pages')



class PageInfo(ResponseSchema):
    number: int = Field(..., description='Current page number')
    size: int = Field(..., description='Number of items per page')
    total: PageTotals
    next_page: Annotated[
        int | None,
        Field(description='Next page number (null if no next page)'),
    ] = None
    previous_page: Annotated[
        int | None,
        Field(description='Previous page number (null if no previous page)'),
    ] = None
    has_previous: bool
    has_next: bool


    @classmethod
    def make(
        cls,
        *,
        page_number: int,
        page_size: int,
        total_items: int,
    ) -> Self:
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        has_previous = page_number > 1
        has_next = page_number < total_pages
        totals = PageTotals(
            pages=total_pages,
            items=total_items,
        )
        next_page = page_number + 1 if has_next else None
        previous_page = page_number - 1 if has_previous else None
        return cls(
            number=page_number,
            size=page_size,
            total=totals,
            next_page=next_page,
            previous_page=previous_page,
            has_previous=has_previous,
            has_next=has_next,
        )

S = TypeVar('S', bound=ResponseSchema)

class PageSchema(ResponseSchema, Generic[S]):

    data: list[S] = Field(..., description='List of items on the current page')
    page: PageInfo = Field(
        ...,
        description='Information about the current page, including pagination details',
    )

    @classmethod
    def from_results(
        cls,
        *,
        data: list[S],
        page_number: int,
        page_size: int,
        total_items: int,
    ) -> Self:
        """
        Creates a PageModel instance from the provided data and pagination parameters.

        Parameters
        ----------
        data : list[S]
            The list of items on the current page.
        page_number : int
            The current page number.
        page_size : int
            The number of items per page.
        total_items : int
            The total number of items across all pages.

        Returns
        -------
        PageModel[S]
            An instance of PageModel containing the paginated data and page info.
        """
        page_info = PageInfo.make(
            page_number=page_number,
            page_size=page_size,
            total_items=total_items,
        )
        return cls(data=data, page=page_info)
