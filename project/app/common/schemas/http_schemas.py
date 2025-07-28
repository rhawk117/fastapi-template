from typing import Annotated, Any, Generic, Self, TypeVar

from pydantic import ConfigDict, Field

from .interface import CustomBaseModel

S = TypeVar('S', bound=CustomBaseModel)


class RequestSchema(CustomBaseModel):
    """
    The base schema and configuration for all request schemas.
    """

    model_config = ConfigDict(
        extra='forbid',
        strict=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )


class ResponseSchema(CustomBaseModel):
    """
    The base schema and configuration for all response schemas.
    """

    pass


class ResponseList(ResponseSchema, Generic[S]):
    size: Annotated[
        int, Field(..., description='The total number of items in the list')
    ]

    is_empty: Annotated[bool, Field(..., description='Whether the list is empty')]

    data: Annotated[
        list[Any], Field(..., description='The list of items returned by the API')
    ]

    @classmethod
    def from_results(cls, data: list[S]) -> Self:
        items = len(data)
        is_empty = items == 0
        return cls(size=items, is_empty=is_empty, data=data)
