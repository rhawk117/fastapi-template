from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings import (
    Settings,
    TomlSettings,
    create_toml_settings,
    load_secret_settings,
)

SECTION_NAME = 'redis'


class RedisSecrets(Settings):
    model_config = SettingsConfigDict(
        env_prefix='REDIS_',
    )

    HOST: str = Field('localhost', description='The host of the Redis server.')
    PORT: int = Field(6379, description='The port of the Redis server.')
    DB: int = Field(0, ge=0, le=15, description='The database number to connect to.')
    USERNAME: str | None = Field(
        None, description='The username for the Redis server, if any.'
    )
    PASSORD: str | None = Field(
        None, description='The password for the Redis server, if any.'
    )


class RedisClientOptions(TomlSettings):
    socket_connect_timeout: float = Field(
        1.0,
        description='The timeout for connecting to the Redis server in seconds.',
    )

    socket_timeout: float = Field(
        5.0,
        description='The timeout for reading/writing to the Redis server in seconds.',
    )

    max_connections: int = Field(
        10,
        description='The maximum number of connections to the Redis server.',
    )

    health_check_interval: int = Field(
        30,
        description='The interval in seconds to check the health of the Redis connection.',
    )


redis_secrets: RedisSecrets = load_secret_settings(RedisSecrets)
redis_options: RedisClientOptions = create_toml_settings(
    settings_class=RedisClientOptions,
    section_name=SECTION_NAME
)
