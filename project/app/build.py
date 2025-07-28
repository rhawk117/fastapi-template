import contextlib
import logging
from collections.abc import AsyncGenerator

from app.core.config import PyprojectConfig, get_app_config
from app.core.log import LoggerOptions, setup_logging
from app.db.core import connect_db, disconnect_db
from app.middleware import register_middleware
from app.redis import client as redis_client
from app.utils.json_response import MsgspecJSONResponse
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def asgi_app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Defines the ASGI lifespan for the FastAPI application.

    - Everything before the `yield` is executed when the application starts.
    - Everything after the `yield` is executed when the application shuts down.

    Parameters
    ----------
    app : FastAPI
        _Must include to match the ASGI lifespan signature._
    Returns
    -------
    AsyncGenerator[None, None]
    """
    await connect_db()
    await redis_client.connect_redis()

    yield

    await disconnect_db()
    await redis_client.disconnect_redis()


def handle_api_documentation(app: FastAPI, allow_openapi_routes: bool) -> None:
    if allow_openapi_routes:
        logger.warning('OpenAPI routes are enabled, disable this option in production')
        app.openapi_url = '/openapi.json'
        app.redoc_url = '/redoc'
        app.docs_url = '/docs'
    else:
        logger.info('OpenAPI routes are disabled.')
        app.openapi_url = None
        app.redoc_url = None
        app.docs_url = None


def create_app() -> FastAPI:
    '''
    Creates and configures the FastAPI application.

    Returns
    -------
    FastAPI
        _the built application_
    '''
    setup_logging(LoggerOptions())
    pyproject_info = PyprojectConfig()  # type: ignore

    app_config = get_app_config()
    app = FastAPI(
        title=pyproject_info.name,
        version=pyproject_info.version,
        description=pyproject_info.description,
        debug=app_config.DEBUG,
        default_response_class=MsgspecJSONResponse,
        lifespan=asgi_app_lifespan,
    )
    logger.info('App instance created.')

    if app_config.DEBUG:
        logger.warning(
            'DEBUG mode is enabled. Disable this option in  a production environment. '
        )

    handle_api_documentation(app, app_config.ALLOW_OPENAPI_ROUTES)

    logger.info('Registering middleware...')
    register_middleware(app, app_config)

    return app
