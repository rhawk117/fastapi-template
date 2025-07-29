from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file_encoding='utf-8'
    )
