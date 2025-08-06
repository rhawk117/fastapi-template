import functools

from pydantic_settings import SettingsConfigDict

from .settings import (
    AppSettings,
    AuthSettings,
    CrossOriginSettings,
    RedisOptions,
    Settings,
    SqlAlchemyOptions,
    TomlConfigFile,
)


class AppConfig(TomlConfigFile):
    model_config = SettingsConfigDict(toml_file='config.toml')

    app: AppSettings
    auth: AuthSettings
    cors: CrossOriginSettings
    sqlalchemy: SqlAlchemyOptions
    redis: RedisOptions

class SecretSettings(Settings):
    model_config = SettingsConfigDict(
        secrets_dir='secrets'
    )


@functools.lru_cache
def get_app_config() -> AppConfig:
    return AppConfig()  # type: ignore
