import functools
import os
from typing import Any, Final

from pydantic_settings import BaseSettings

from app.core import path_utils

from ..exceptions import BuildFailedError
from . import toml_utils
from .app import AppConfig

TOML_CONFIG_FILE: Final[str] = 'config.toml'


@functools.lru_cache
def get_toml_config_file() -> dict:
    app_root = path_utils.get_app_root()
    config_file = app_root / TOML_CONFIG_FILE
    return toml_utils.read_toml(config_file)


def create_toml_settings(settings_class: type[BaseSettings], section_name: str) -> Any:
    """
    Create a settings instance from a TOML section.

    Parameters
    ----------
    settings_cls : type[TomlSettings]
    section_name : str

    Returns
    -------
    TomlSettings
    """
    toml_config = get_toml_config_file()
    return toml_utils.section_to_settings(
        settings_cls=settings_class,
        section_name=section_name,
        toml_data=toml_config
    )


_app_config: Final[AppConfig] = create_toml_settings(
    settings_class=AppConfig,
    section_name='app'
)


def load_secret_settings(
    settings_class: type[BaseSettings],
    *,
    testing_fallback_cls: type[BaseSettings] | None = None,
) -> Any:
    app_env = _app_config.env_file

    if not app_env or not os.path.exists(app_env):
        raise BuildFailedError(
            f'Environment file {app_env} does not exist. '
            'Please ensure the environment file is present.'
        )

    if testing_fallback_cls and _app_config.testing:
        return testing_fallback_cls()

    return settings_class(
        _env_file=app_env,
    )


def get_app_settings() -> AppConfig:
    """
    Get the application settings.

    Returns
    -------
    AppConfig
    """
    return _app_config
