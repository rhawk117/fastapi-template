import dataclasses
from pathlib import Path

from backend.common.types import LogLevelNames


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class LogFilesConfig:
    error_log_file: str = dataclasses.field(default='error.log')
    access_log_file: str = dataclasses.field(default='access.log')

    error_log_level: LogLevelNames = dataclasses.field(default='ERROR')
    access_log_level: LogLevelNames = dataclasses.field(default='INFO')


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class LogFileOptions:
    format: str = dataclasses.field(
        default='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    enqueue: bool = dataclasses.field(default=True)
    rotation: str = dataclasses.field(default='00:00')
    retention: str = dataclasses.field(default='7 days')
    directory: Path = dataclasses.field(default=Path('logs'))


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class LoggerOptions:
    stdout_level: LogLevelNames = dataclasses.field(default='INFO')
    files_config: LogFilesConfig = dataclasses.field(default_factory=LogFilesConfig)
    file_options: LogFileOptions = dataclasses.field(default_factory=LogFileOptions)
