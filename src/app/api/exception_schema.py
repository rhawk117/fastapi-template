from typing import Any, Self

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import ErrorDetails


class _BaseHttpError(BaseModel):
    message: str = Field(
        ...,
        description='Description of the error that occured.',
    )
    success: bool = Field(
        default=False,
        description='Always False, Indicates the request failed.',
    )


class HttpErrorModel(_BaseHttpError):
    """
    Represents a generic HTTP error response model.
    """

    details: dict[str, Any] | None = Field(
        default=None,
        description='Additional details that may be included to describe the error',
    )


def join_field_loc(loc: tuple[str | int, ...]) -> str:
    if not loc:
        return ''
    return '.'.join(str(x) for x in loc)


class PydanticErrorMeta(BaseModel):
    field: str = Field(..., description='The field that caused the error')
    message: str = Field(..., description='The error message')
    type: str = Field(..., description='The type of error')


def parse_pydantic_error(
    details: ErrorDetails | Any,
) -> PydanticErrorMeta:
    field = join_field_loc(details.get('loc', ()))
    message = details.get('msg', 'Invalid data.')
    error_type = details.get('type', 'Unknown')

    return PydanticErrorMeta(
        field=field,
        message=message,
        type=error_type,
    )


def collect_validation_errors(
    exc: ValidationError | RequestValidationError,
) -> list[PydanticErrorMeta]:
    """
    Normalizes the validation error from Pydantic or FastAPI

    Parameters
    ----------
    err : ValidationError | RequestValidationError

    Returns
    -------
    list[PydanticErrorMeta]
    """
    error_list = []
    for details in exc.errors():
        error_list.append(parse_pydantic_error(details))

    return error_list


class HttpValidationErrorModel(_BaseHttpError):
    """
    Represents a validation error response model.
    """

    errors: list[PydanticErrorMeta] = Field(
        ...,
        description='List of parsed validation errors',
    )

    @classmethod
    def from_validation_error(
        cls,
        exc: ValidationError | RequestValidationError,
        *,
        message: str | None = None,
    ) -> Self:
        if not message:
            message = 'One or more of the fields provided is invalid.'

        errors = collect_validation_errors(exc)
        return cls(
            errors=errors,
            message=message,
        )
