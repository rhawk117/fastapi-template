import dataclasses
from typing import Annotated

from app.core.config import BaseAppSettings
from pydantic import Field


@dataclasses.dataclass(slots=True)
class RedisConnectionOptions:
    socket_connect_timeout: float = 5.0
    socket_timeout: float = 5.0
    max_connections: int = 10
    health_check_interval: float = 10.0


class RedisConfig(BaseAppSettings):
    REDIS_HOST: Annotated[
        str, Field(default='localhost', description='The hostname of the Redis server.')
    ]

    REDIS_PORT: Annotated[
        int,
        Field(
            default=6379,
            description='The port number on which the Redis server is running.',
        ),
    ]

    REDIS_DB: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            le=15,
            description='The database number to connect to on the Redis server.',
        ),
    ]

    REDIS_PASSWORD: Annotated[
        str | None,
        Field(
            default=None,
            description='The password for the Redis server, if authentication is required.',
        ),
    ]


redis_config = RedisConfig()  # type: ignore
redis_client_options = RedisConnectionOptions()  # type: ignore
