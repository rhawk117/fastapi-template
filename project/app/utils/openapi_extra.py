from app.common.schemas import (
    CustomBaseModel,
    HTTPErrorSchema,
    HTTPValidationErrorSchema,
)
from fastapi.routing import APIRoute
from pydantic import BaseModel

# A descriptive wrapper for documenting API responses for better OpenAPI spec generation
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


def ResponseDoc(
    description: str,
    status_code: int = 200,
    *,
    model: type[CustomBaseModel],
    headers: dict | None = None,
    title: str | None = None,
) -> dict:
    if title:
        description += f'## {title}\n{description}'

    return {
        status_code: {
            'description': description,
            'model': model,
            'headers': headers or {},
        }
    }


def ErrorDoc(
    description: str,
    status_code: int = 400,
    *,
    model: type[BaseModel] | None = None,
    headers: dict | None = None,
    title: str | None = None,
) -> dict:
    if not model:
        model = HTTPErrorSchema

    return ResponseDoc(
        description=description,
        status_code=status_code,
        model=model,  # type: ignore
        headers=headers,
        title=title,
    )


def ResponseList(responses: dict) -> dict:
    combined_responses = {}
    for status_code, response in responses.items():
        if status_code in combined_responses:
            combined_responses[status_code].update(response)
        else:
            combined_responses[status_code] = response

    return combined_responses


def SchemaError(
    description: str,
    status_code: int = 422,
    *,
    model: type[BaseModel] | None = None,
    headers: dict | None = None,
    title: str | None = None,
) -> dict:
    if not model:
        model = HTTPValidationErrorSchema

    return ErrorDoc(
        description=description,
        status_code=status_code,
        model=model,  # type: ignore
        headers=headers,
        title=title,
    )


def NotFound(resource: str, status_code: int = 404) -> dict:
    return ErrorDoc(
        description=f'{resource} not found.',
        status_code=status_code,
        model=HTTPErrorSchema,
        title='Not Found',
    )
