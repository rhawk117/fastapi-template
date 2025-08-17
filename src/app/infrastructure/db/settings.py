from typing import Literal

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings import (
    Settings,
    TomlSettings,
    create_toml_settings,
    load_secret_settings,
)


class SQLAlchemyOptions(TomlSettings):
    """SQLite settings for the ORM plugin."""

    pool_recycle: int = Field(
        default=3600,
        description='The number of seconds to recycle the connection pool.',
    )

    pool_timeout: int = Field(
        default=30,
        description='The number of seconds to wait for a connection from the pool.',
    )

    pool_size: int = Field(
        default=10,
        description='The number of connections to keep in the pool.',
    )

    max_overflow: int = Field(
        default=10,
        description='The maximum number of connections to create beyond the pool size.',
    )

    pool_use_lifo: bool = Field(
        default=False,
        description='Whether to use LIFO instead of FIFO for the connection pool.',
    )

    pool_pre_ping: Literal[True] = True
    future: Literal[True] = True

    run_seed: bool = Field(
        default=False,
        description='Whether to run the seed script on startup.',
    )

    echo: bool = Field(
        default=False,
        description='Whether to echo SQL statements.',
    )

    expire_on_commit: bool = Field(
        default=False,
        description='Whether to expire objects on commit.',
    )

    autoflush: bool = Field(
        default=False,
        description='Whether to autoflush the session.',
    )

    @property
    def engine_kwargs(self) -> dict:
        return self.model_dump(
            exclude={'run_seed', 'echo', 'expire_on_commit', 'autoflush'},
        )


class DatabaseSecrets(Settings):
    model_config = SettingsConfigDict(env_prefix='DATABASE_')

    FILE_NAME: str = Field(
        default=':memory:', description='The SQLite database file path.'
    )

    TIMEOUT: int = Field(
        default=30,
        description='The number of seconds to wait for a connection before timing out.',
    )

    DIRECTORY: str = Field(
        default='instance',
        description='The directory where the SQLite database file is located.',
    )

    ECHO: bool = Field(
        default=False,
        description='Whether to echo SQL statements.',
    )

    DRIVER_NAME: str = Field(
        default='sqlite+aiosqlite',
        description='The database driver name.',
    )

    @property
    def database(self) -> str:
        return (
            f'{self.DIRECTORY}/{self.FILE_NAME}'
            if self.FILE_NAME != ':memory:'
            else self.FILE_NAME
        )


sqlalchemy_options: SQLAlchemyOptions = create_toml_settings(
    settings_class=SQLAlchemyOptions, section_name='sqlalchemy'
)
db_secrets: DatabaseSecrets = load_secret_settings(settings_class=DatabaseSecrets)
