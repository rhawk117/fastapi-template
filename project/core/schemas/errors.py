from typing import Annotated, Any, Self

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import ErrorDetails


class ValidationErrorSchema(BaseModel):
    field: Annotated[str, Field(..., description='The field that caused the error')]
    message: Annotated[str, Field(..., description='The error message')]
    type: Annotated[str, Field(..., description='The type of error')]

    @classmethod
    def create(cls, details: ErrorDetails | Any) -> Self:
        field_name = '.'.join(str(loc) for loc in details.get('loc', []))
        message = details.get('msg', 'Invalid data.')
        error_type = details.get('type', 'Unknown')
        return cls(field=field_name, message=message, type=error_type)

    def __repr__(self) -> str:
        return str(self)


def collect_validation_errors(
    exc: ValidationError | RequestValidationError,
) -> list[ValidationErrorSchema]:
    """
    Normalizes the validation error from Pydantic or FastAPI

    Parameters
    ----------
    err : ValidationError | RequestValidationError

    Returns
    -------
    list[ValidationErrorSchema]
    """
    error_list = []
    for details in exc.errors():
        error_data = ValidationErrorSchema.create(details=details)
        error_list.append(error_data)

    return error_list


class HTTPErrorSchema(BaseModel):
    message: Annotated[str, Field(..., description='Description of the error')]
    success: bool = False
    details: dict[str, Any] | None = None


class HTTPValidationErrorSchema(BaseModel):
    errors: list[ValidationErrorSchema]
    message: str = 'Validation failed'
    success: bool = False

    @classmethod
    def from_validation_error(
        cls,
        exc: ValidationError | RequestValidationError
    ) -> Self:
        errors = collect_validation_errors(exc)
        return cls(errors=errors)
