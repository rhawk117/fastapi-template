import functools
from typing import Any, Self, get_origin

from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


def _parse_sequence(value: str, *, is_hashset: bool = False) -> set[str] | list[str]:
    seq = [item.strip() for item in value.split(',') if item.strip()]
    if is_hashset:
        return set(seq)
    return seq


class _EnvSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        field_origin = get_origin(field.annotation)
        is_hashset = field_origin is set

        if field_origin is list or is_hashset:
            return _parse_sequence(value, is_hashset=is_hashset)

        return super().prepare_field_value(field_name, field, value, value_is_complex)


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        extra='ignore',
        validate_assignment=True,
        case_sensitive=False,
    )

    @classmethod
    def cached_factory(cls):
        @functools.lru_cache
        def _get_cached_settings() -> Self:
            return cls()

        return _get_cached_settings


class EnvConfig(BaseConfig):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            _EnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


class YamlSettingsLoader(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(settings_cls),
            init_settings,
            _EnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )
