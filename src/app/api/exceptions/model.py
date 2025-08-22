from typing import Self

from fastapi.exceptions import RequestValidationError
from pydantic import Field, ValidationError

from app.core.schema import PydanticSchema
from app.utils.validation_errors import FieldDetails, parse_validation_error


class HttpErrorModel(PydanticSchema):
    message: str = Field(
        'Oops! Something went wrong.', description='A message describing the error'
    )
    success: bool = False
    extra: dict | None = None


class HttpValidationErrorModel(PydanticSchema):
    message: str = Field(
        'Invalid request parameters.',
        description='A message describing the validation error',
    )
    success: bool = False
    details: list[FieldDetails] = Field(
        ..., description='A list of details about the validation errors'
    )

    @classmethod
    def from_validation_error(
        cls,
        exc: ValidationError | RequestValidationError,
        *,
        message: str = 'Invalid request parameters.',
    ) -> Self:
        details = parse_validation_error(exc)
        return cls(details=details, message=message)
