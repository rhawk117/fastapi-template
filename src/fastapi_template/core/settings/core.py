import functools

from pydantic_settings import (
    SettingsConfigDict,
)

from fastapi_template.core.settings.file_loader import TomlSettingsLoader
from fastapi_template.core.settings.secrets import SecretSettings

from .config_file import (
    AppSettings,
    AuthSettings,
    LoggerSettings,
    MiddlewareSettings,
    RedisClientOptions,
    SQLAlchemyOptions,
)


class SettingsFile(TomlSettingsLoader):
    """
    The loaded static settings of the app
    """

    model_config = SettingsConfigDict(toml_file='settings.toml')
    app: AppSettings
    logging: LoggerSettings
    auth: AuthSettings
    middleware: MiddlewareSettings
    sqlalchemy: SQLAlchemyOptions
    redis_client: RedisClientOptions


@functools.lru_cache(maxsize=1)
def get_config_file() -> SettingsFile:
    return SettingsFile()  # type: ignore


@functools.lru_cache(maxsize=1)
def get_secrets() -> SecretSettings:
    settings = get_config_file()
    return SecretSettings(_env_file=settings.app.env_file)  # type: ignore
