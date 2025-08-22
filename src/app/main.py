import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.adapters import db, log, redis_client
from app.core import settings
from app.exc_handler import HttpErrorHandler
from app.spec import get_api_spec

# NOTE: in both on_startup, on_shutdown the app instance must be included
# even if it is not used to match method signature


def register_exception_handlers(app: FastAPI) -> None:
    handler = HttpErrorHandler()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await handler.handle_http_exception(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return await handler.handle_request_validation_error(request, exc)


def register_middleware(app: FastAPI) -> None:
    middleware_settings = settings.get_app_settings().middleware

    app.add_middleware(
        CorrelationIdMiddleware,
        header_name=middleware_settings.correlation_id.HEADER_NAME,
        update_request_header=middleware_settings.correlation_id.UPDATE_REQUEST_HEADER,
        generator=middleware_settings.correlation_id.id_factory,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=middleware_settings.cors.ALLOW_ORIGINS,
        allow_credentials=middleware_settings.cors.ALLOW_CREDENTIALS,
        allow_methods=middleware_settings.cors.ALLOW_METHODS,
        allow_headers=middleware_settings.cors.ALLOW_HEADERS,
    )

    if middleware_settings.MIDDLEWARE_ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=middleware_settings.MIDDLEWARE_ALLOWED_HOSTS,
        )


@asynccontextmanager
async def asgi_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Defines what should happen when the app first starts and when it shuts down
    the app start routine is before the "yield" and the shutdown routine is after the "yield"

    Arguments:
        app {FastAPI} -- the app instance, required even if not used
    """

    await db.connect_db()
    await redis_client.connect_redis()

    # ^ app startup

    yield

    # v app shutdown

    await db.disconnect_db()
    await redis_client.disconnect_redis()


def disable_docs(app: FastAPI) -> None:
    app.openapi_url = None
    app.docs_url = None
    app.redoc_url = None


def create_app() -> FastAPI:
    """
    Creates the FastAPI instance and returns the
    created app instance.

    Returns:
        FastAPI -- the API instance
    """
    log.setup_logging()
    config = settings.get_app_settings()
    logger = logging.getLogger(__name__)
    api_spec = get_api_spec()
    config = settings.get_app_settings()

    app = FastAPI(
        **api_spec.get_fastapi_kwargs(),
        lifespan=asgi_lifespan,
        debug=config.app.DEBUG,
    )

    if app.debug:
        logger.warning('Debug mode is enabled, disable in production.')

    if not config.app.ALLOW_DOCS:
        disable_docs(app)
        logger.info('OpenAPI documentation is disabled.')
    else:
        logger.info('Documentation routes enabled, disable in production.')

    logger.info('App instance created, registering middleware and exception handlers.')
    register_middleware(app)
    register_exception_handlers(app)
    logger.info('Middleware initialized, adding API routes.')

    # app.include_router(api_router)

    logger.info('API routes registered successfully, app build successful.')
    return app
