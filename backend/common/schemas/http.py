from typing import TypeVar

from pydantic import ConfigDict

from backend.core.schema import CustomBaseModel

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
