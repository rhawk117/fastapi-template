import contextlib
import logging
from collections.abc import AsyncGenerator

from app.core.config import PyprojectConfig, get_app_config
from app.core.log import LoggerOptions, setup_logging
from app.db.core import connect_db, disconnect_db
from app.middleware import register_middleware
from app.redis import connect_redis, disconnect_redis
from app.utils.json_response import MsgspecJSONResponse
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def asgi_app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_db()
    await connect_redis()

    yield

    await disconnect_db()
    await disconnect_redis()


def create_app() -> FastAPI:
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

    if app_config.ALLOW_OPENAPI_ROUTES:
        logger.warning('OpenAPI routes are enabled, disable this option in production')
        app.openapi_url = '/openapi.json'
        app.redoc_url = '/redoc'
        app.docs_url = '/docs'
    else:
        logger.info('OpenAPI routes are disabled. ')
        app.openapi_url = None
        app.redoc_url = None
        app.docs_url = None

    logger.info('Registering middleware...')
    register_middleware(app, app_config)

    return app
