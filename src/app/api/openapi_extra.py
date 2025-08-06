from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.api.exception_schema import (
    HttpErrorModel,
    HttpValidationErrorModel,
)

# A descriptive wrappers for documenting API responses for better OpenAPI spec generation
# for your OpenAPI Client generator.


def create_operation_id(route: APIRoute) -> str:
    """
    Generates a unique id for the route to help normalize
    the API service names.
    https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function

    Returns:
        str -- the adjusted operation ID
    """
    return f'{route.tags[0]}-{route.name}'


def HTTPError(
    description: str,
    *,
    model: type[BaseModel] | None = None,
    headers: dict | None = None,
) -> dict:
    if not model:
        model = HttpErrorModel

    return {
        'model': model,
        'description': description,
        'headers': headers or {},
    }


def SchemaError(
    description: str,
    *,
    model: type[BaseModel] | None = None,
    headers: dict | None = None,
) -> dict:
    if not model:
        model = HttpValidationErrorModel

    return HTTPError(
        description=description,
        model=model,  # type: ignore
        headers=headers,
    )
