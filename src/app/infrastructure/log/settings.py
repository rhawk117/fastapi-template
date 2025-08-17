from typing import Literal

from pydantic import BaseModel, Field

from app.core.settings import TomlSettings, create_toml_settings

LoguruLevels = Literal[
    'TRACE',
    'DEBUG',
    'INFO',
    'SUCCESS',
    'WARNING',
    'ERROR',
    'CRITICAL',
]

LoguruCompression = Literal['zip', 'tar', 'gz', 'bz2', 'xz', 'none']


class JsonLoggerSink(BaseModel):
    name: str = Field(
        ...,
        description='The name of the logger and sub directory directory to store files',
    )
    level: LoguruLevels = Field(
        'INFO',
        description='The minimum level to log to this file',
    )


class LoggerSettings(TomlSettings):
    json_loggers: list[JsonLoggerSink] | None = Field(
        default=None, description='A mapping of the default json loggers to initialize'
    )

    stdout_level: LoguruLevels = Field(
        'TRACE',
        description='The minimum level to log to stdout',
    )

    directory: str = Field(
        'logs',
        description='The base directory to store log files',
    )

    rotation_mb: int = Field(
        10,
        description='The size in megabytes to rotate log files',
        ge=1,
        le=1000,
    )

    retention_days: int = Field(
        7,
        description='The number of days to retain log files',
        ge=1,
        le=90,
    )

    compression: LoguruCompression = Field(
        'zip',
        description='The compression method to use for rotated log files',
    )

    @property
    def stdout_format(self) -> str:
        return (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
            '<level>{level: <8}</level> | '
            'cid=<cyan>{extra[correlation_id]}</cyan> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        )


log_settings: LoggerSettings = create_toml_settings(
    LoggerSettings,
    section_name='logs',
)
