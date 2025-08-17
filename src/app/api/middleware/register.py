from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .exception_handler import register_exception_handlers
from .request_logging import RequestLoggingMiddleware
from .settings import middleware_settings


def register_middleware(app: FastAPI) -> None:
    """Registers the middleware to the API instance

    Arguments:
        app {FastAPI} -- the API instance
    """
    # NOTE: always add CorrelationId first, it attaches the correlation ID
    # to the request header
    app.add_middleware(
        CorrelationIdMiddleware,
        **middleware_settings.correlation_id.model_dump(),
    )

    app.add_middleware(
        CORSMiddleware,
        **middleware_settings.cors.model_dump(),
    )

    app.add_middleware(
        RequestLoggingMiddleware,
        logger_name='api.request_logger',
        correlation_id_header=middleware_settings.correlation_id.header_name,
    )

    if middleware_settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=middleware_settings.allowed_hosts,
        )

    register_exception_handlers(app)
