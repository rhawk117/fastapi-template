from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_template.core import settings
from fastapi_template.core.response_class import MsgspecJSONResponse
from fastapi_template.infrastructure.db import DatabaseConnection
from fastapi_template.infrastructure.redis import RedisClient


@asynccontextmanager
async def asgi_lifespan(app: FastAPI):
    config = settings.get_config_file()
    secrets = settings.get_secrets()

    await DatabaseConnection.connect(options=config.sqlalchemy, secrets=secrets)
    await RedisClient.connect(options=config.redis_client, secrets=secrets)
    yield

    await DatabaseConnection.disconnect()
    await RedisClient.disconnect()


def create_app() -> FastAPI:
    config = settings.get_config_file()

    docs_url = config.app.get_docs_urls()

    app = FastAPI(
        title=config.app.name,
        description=config.app.description,
        version=config.app.version,
        debug=config.app.debug,
        lifespan=asgi_lifespan,
        response_class=MsgspecJSONResponse,
        **docs_url
    )


    return app