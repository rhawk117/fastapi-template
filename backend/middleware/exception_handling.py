import logging
import traceback

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

from backend.common.schemas import HTTPErrorSchema, HTTPValidationErrorSchema
from backend.utils.json_response import MsgspecJSONResponse

error_logger = logging.getLogger('error')

__all__ = ['register_exception_handlers']


async def log_http_error(request: Request, exc: HTTPException) -> None:
    base_log_message = (
        f'HTTP error occurred: {exc.detail} | '
        f'Status code: {exc.status_code} | '
        f'Path: {request.url.path}'
    )

    if exc.status_code < 500:
        error_logger.warning(
            base_log_message,
            extra={
                'request_id': request.headers.get('X-Request-ID', 'unknown'),
                'method': request.method,
            },
            exc_info=exc,
        )
        return

    formatted_tracback = ''.join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )

    log_message = f'{base_log_message}\n{formatted_tracback}'

    error_logger.error(
        log_message,
        extra={
            'request_id': request.headers.get('X-Request-ID', 'unknown'),
            'method': request.method,
        },
        exc_info=exc,
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> MsgspecJSONResponse:
    await log_http_error(request, exc)

    response_content = HTTPErrorSchema(
        message=exc.detail,
        success=False,
    )

    error_headers = exc.headers or {}

    return MsgspecJSONResponse(
        status_code=exc.status_code,
        content=response_content.model_dump(),
        headers={
            'X-Request-ID': request.headers.get('X-Request-ID', 'unknown'),
            **error_headers,
        },
    )


async def http_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> MsgspecJSONResponse:
    response_content = HTTPValidationErrorSchema.from_validation_error(exc)
    error_logger.warning(
        f'A validation error occured at {request.url.path}: {response_content.errors}',
        extra={
            'request_id': request.headers.get('X-Request-ID', 'unknown'),
            'method': request.method,
            'errors': response_content.errors,
        },
        exc_info=exc,
    )

    return MsgspecJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content.model_dump(),
        headers={
            'X-Request-ID': request.headers.get('X-Request-ID', 'unknown'),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> MsgspecJSONResponse:
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> MsgspecJSONResponse:
        return await http_validation_exception_handler(request, exc)
