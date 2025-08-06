from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import ErrorDetails


def join_field_loc(loc: tuple[str | int, ...]) -> str:
    if not loc:
        return ''
    return '.'.join(str(x) for x in loc)


class FieldDetails(BaseModel):
    field: str = Field(..., description='The field that caused the error')
    message: str = Field(..., description='The error message')
    type: str = Field(..., description='The type of error')


def parse_pydantic_details(
    details: ErrorDetails | Any,
) -> FieldDetails:
    field = join_field_loc(details.get('loc', ()))
    message = details.get('msg', 'Invalid data.')
    error_type = details.get('type', 'Unknown')

    return FieldDetails(
        field=field,
        message=message,
        type=error_type,
    )


def collect_validation_errors(
    exc: ValidationError | RequestValidationError,
) -> list[FieldDetails]:
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
        error_list.append(parse_pydantic_details(details))

    return error_list
