import functools
from pathlib import Path
from typing import Any, Final, Self

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_FILE_NAME: Final[str] = 'config.yml'


@functools.lru_cache(maxsize=1)
def get_config_yaml() -> dict[str, Any]:
    global CONFIG_FILE_NAME
    config_path = Path(CONFIG_FILE_NAME)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE_NAME}' not found.")

    config_contents = config_path.read_text(encoding='utf-8')

    try:
        contents = yaml.safe_load(config_contents)
    except yaml.YAMLError as e:
        raise RuntimeError(f'Error parsing YAML configuration: {e}')

    return contents


class YMLSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore'
    )

    @classmethod
    def load_config(
        cls,
        *,
        yaml_key: str,
        overrides: dict[str, Any] | None = None
    ) -> Self:
        config = get_config_yaml()
        if yaml_key not in config:
            raise RuntimeError(f"Section '{yaml_key}' not found in configuration.")

        settings_kwargs = config[yaml_key]
        if overrides:
            settings_kwargs.update(overrides)

        try:
            instance = cls(**settings_kwargs)
        except Exception as e:
            raise RuntimeError(f"Error loading section '{yaml_key}': {e}") from e

        return instance
