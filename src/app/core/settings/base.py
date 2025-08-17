from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        extra='ignore',
        validate_assignment=True,
        case_sensitive=False,
    )


class TomlSettings(Settings): ...
