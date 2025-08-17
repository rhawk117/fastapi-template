import traceback

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.infrastructure import log

from ..exceptions.model import HttpErrorModel, HttpValidationErrorModel
from ..response_class import MsgspecJSONResponse


class HttpErrorHandler:
    """
    Handles HTTP exceptions raised by FastAPI and logs them using the configured logger.
    """

    def __init__(
        self,
        *,
        logger_name: str,
        level: str,
    ) -> None:
        self._json_logger_name: str = logger_name
        self._level: str = level

    def register_logger(self) -> None:
        """Registers the logger for this handler."""
        log.get_json_registry().register(self._json_logger_name, self._level)

    @property
    def logger(self):
        """Returns the logger for this handler."""
        return log.get_json_logger(self._json_logger_name)

    def _infer_exception_details(
        self, exception: HTTPException | RequestValidationError
    ) -> tuple[int, str]:
        """Processes the exception to determine the status code and detail message."""
        if isinstance(exception, RequestValidationError):
            return (
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                'Validation error occurred, client provided bad data',
            )
        elif isinstance(exception, HTTPException):
            return exception.status_code, exception.detail
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR, 'An unexpected error occurred'

    def _get_500_error_details(
        self, exc: HTTPException | RequestValidationError
    ) -> dict:
        traceback_string = ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        return {
            'traceback': traceback_string,
            'exception_info': str(exc),
        }

    async def log_error(
        self,
        request: Request,
        exc: HTTPException | RequestValidationError,
        *,
        message: str | None = None,
        extra: dict | None = None,
    ) -> None:
        """logs the error according to the exception type with json data"""
        logger = self.logger
        status_code, detail = self._infer_exception_details(exc)
        logged_data = {
            'method': request.method,
            'url': str(request.url),
            'status_code': status_code,
            'detail': detail,
            'headers': request.headers,
            'exception_cls': exc.__class__.__name__,
        }

        if extra:
            logged_data.update(extra)

        if status_code >= 500:
            logged_data.update(self._get_500_error_details(exc))

        if not message:
            message = (
                f'An HTTP error occurred at {request.url} with '
                f'status code {status_code}'
            )

        logger.error(
            message,
            exc_info=exc,
            extra=logged_data,
        )

    async def handle_http_exception(
        self, request: Request, exc: HTTPException
    ) -> MsgspecJSONResponse:
        """for basic HTTP exceptions raised by FastAPI."""
        json = HttpErrorModel(message=exc.detail).model_dump()
        await self.log_error(request, exc, message='HTTP Exception occurred')
        return MsgspecJSONResponse(
            status_code=exc.status_code, content=json, headers=exc.headers
        )

    async def handle_request_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> MsgspecJSONResponse:
        """handles request validation errors, pydantic validation errors."""
        json = HttpValidationErrorModel.from_validation_error(exc).dump()
        extras = {
            'pydantic_detail': exc.errors(),
            'pydantic_parsed': json,
        }
        await self.log_error(
            request,
            exc,
            message='Request validation error, client provided bad data',
            extra=extras,
        )

        return MsgspecJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=json,
        )


def register_exception_handlers(
    app: FastAPI,
    *,
    logger_name: str | None = None,
    level: str | None = None,
) -> None:
    exception_handler = HttpErrorHandler(
        logger_name=logger_name or 'http_error_handler',
        level=level or 'ERROR',
    )
    exception_handler.register_logger()

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> MsgspecJSONResponse:
        return await exception_handler.handle_request_validation_error(request, exc)

    @app.exception_handler(HTTPException)
    async def _basic_http_handler(
        request: Request, exc: HTTPException
    ) -> MsgspecJSONResponse:
        return await exception_handler.handle_http_exception(request, exc)
