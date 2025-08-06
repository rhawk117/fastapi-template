import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.config import SecretSettings


class DatabaseSettings(SecretSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='DB_')

    url: str = Field(..., description='The URL to the database')
    pool_recycle: int = Field(
        default=3600,
        description='Number of seconds after which a connection is recycled',
    )
    pool_size: int = Field(
        default=5,
        description='Number of connections to keep in the pool',
    )
    max_overflow: int = Field(
        default=10,
        description='Number of connections that can be created beyond the pool size',
    )
    pool_timeout: int = Field(
        default=30,
        description='Number of seconds to wait before giving up on getting a connection from the pool',
    )
    pool_pre_ping: bool = Field(
        default=True,
        description='Whether to check connections before using them from the pool',
    )
    pool_use_lifo: bool = Field(
        default=True,
        description='Whether to use LIFO (Last In, First Out) for pool management',
    )
    future: bool = Field(
        default=True,
        description='Use the future API for SQLAlchemy, reccomended for fastapi',
    )
    echo: bool = Field(
        default=False,
        description='Enable SQLAlchemy logging for all statements',
    )

    @property
    def engine_args(self) -> dict:
        return self.model_dump(exclude={'url'})


@functools.lru_cache
def get_db_settings() -> DatabaseSettings:
    return DatabaseSettings()  # type: ignore
