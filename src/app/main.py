import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import log
from app.core.config import settings
from app.api.response_class import MsgspecJSONResponse
from app.db.connection import connect_db, disconnect_db
from app.middleware.request_logging import RequestLoggingMiddleware
from app.redis.client import redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def asgi_lifespan(app: FastAPI):
    logger.info('ASGI Lifespan started')
    await connect_db()

    logger.info('Connected to the database, initializing Redis client')
    await redis_client.connect()
    logger.info('Redis client connected, app startup complete')

    yield
    logger.info('ASGI Lifespan shutdown started, disconnecting from database and Redis')
    await disconnect_db()
    logger.info('Disconnected from the database')
    await redis_client.disconnect()


def register_middleware(app: FastAPI) -> None:
    mw_config = settings.get_config().middleware

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware, header_name='X-Request-ID')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=mw_config.cors.allow_origins,
        allow_credentials=mw_config.cors.allow_credentials,
        allow_methods=mw_config.cors.allow_methods,
        allow_headers=mw_config.cors.allow_headers,
    )

    logger.info('Middleware registered successfully')


def create_app() -> FastAPI:
    config = settings.get_config()

    log.configure_logger('INFO')
    log.configure_file_loggers(
        app_level='INFO',
        access_level='INFO',
        error_level='WARNING'
    )

    app = FastAPI(
        **config.app.fastapi_kwargs,
        lifespan=asgi_lifespan,
        response_class=MsgspecJSONResponse,
    )

    register_middleware(app)

    return app
