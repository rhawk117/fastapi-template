from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_template.core import config
from fastapi_template.api.response_class import MsgspecJSONResponse
from fastapi_template.infrastructure.db import DatabaseConnection
from fastapi_template.infrastructure.redis import RedisClient


@asynccontextmanager
async def asgi_lifespan(app: FastAPI):
    config = config.get_config_file()
    secrets = config.get_secrets()

    await DatabaseConnection.connect(options=config.sqlalchemy, secrets=secrets)
    await RedisClient.connect(options=config.redis_client, secrets=secrets)
    yield

    await DatabaseConnection.disconnect()
    await RedisClient.disconnect()


def create_app() -> FastAPI:
    config = config.get_config_file()

    app = FastAPI(
        **config.app.fastapi_kwargs,
        lifespan=asgi_lifespan,
        response_class=MsgspecJSONResponse,
    )

    return app
