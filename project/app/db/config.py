import dataclasses
from typing import Annotated

from app.core.config import BaseAppSettings
from pydantic import Field


@dataclasses.dataclass(slots=True)
class ORMEngineOptions:
    # The number of seconds to recycle the connection pool.
    pool_recycle: int = dataclasses.field(default=3600)
    # The number of seconds to wait for a connection from the pool.
    pool_timeout: int = dataclasses.field(default=30)
    # The number of connections to keep in the pool.
    pool_size: int = dataclasses.field(default=10)
    # The maximum number of connections to create beyond the pool size.
    max_overflow: int = dataclasses.field(default=10)
    # Whether to use LIFO instead of FIFO for the connection pool.
    pool_use_lifo: bool = dataclasses.field(default=False)
    # Whether to enable pre-ping for the connection pool.
    pool_pre_ping: bool = dataclasses.field(default=True)
    # Whether to enable the connection pool.
    future: bool = dataclasses.field(default=True)


class DatabaseConfig(BaseAppSettings):
    DATABASE_FILE_NAME: Annotated[
        str,
        Field(
            default='app.db',
            description='The name of the database file.',
        ),
    ]
    SQLALCHEMY_ECHO: Annotated[
        bool, Field(default=False, description='Whether to echo SQL statements.')
    ]
    DATABASE_DIRECTORY: Annotated[
        str,
        Field(
            default='instance',
            description='The directory where the database file is located.',
        ),
    ]

    @property
    def database(self) -> str:
        return f'{self.DATABASE_DIRECTORY}/{self.DATABASE_FILE_NAME}'


database_config = DatabaseConfig()  # type: ignore
engine_options = ORMEngineOptions()
