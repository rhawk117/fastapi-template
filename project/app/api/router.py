from app.api.auth.router import auth_router
from app.utils.openapi_extra import (
    ErrorDoc,
    ResponseList,
    SchemaError,
    create_operation_id,
)
from fastapi import APIRouter

api_router = APIRouter(
    prefix='/api',
    generate_unique_id_function=create_operation_id,
    responses=ResponseList(
        [
            SchemaError(
                'Request body is invalid causing a 422 Unprocessable Entity error.'
            ),
            ErrorDoc(
                status_code=500,
                title='Internal Server Error',
                description='An unexpected error occurred on the server.',
            ),
        ]
    ),
)

api_router.include_router(auth_router, prefix='/auth', tags=['auth'])

