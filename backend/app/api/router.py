from fastapi import APIRouter, status

from backend.utils.openapi_extra import (
    HTTPError,
    SchemaError,
    create_operation_id,
)

from .auth.router import auth_router
from .users.router import user_router

api_router = APIRouter(
    prefix='/api',
    generate_unique_id_function=create_operation_id,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: SchemaError(
            'Request body is invalid causing a 422 Unprocessable Entity error.'
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: HTTPError(
            'An unexpected error occurred on the server.',
        ),
    },
)

api_router.include_router(auth_router, prefix='/auth', tags=['auth'])
api_router.include_router(user_router, prefix='/users', tags=['users'])
