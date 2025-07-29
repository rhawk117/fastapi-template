from __future__ import annotations

import dataclasses
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from .handlers import LoguruInterceptor
from .options import LogFileOptions, LogFilesConfig, LoggerOptions

if TYPE_CHECKING:
    from loguru import Logger


def setup_logging(options: LoggerOptions) -> None:
    logging.root.handlers = [LoguruInterceptor(logger)]
    logging.root.setLevel(options.stdout_level)

    forbid_progagate = ('uvicorn.access', 'watchfiles.main')
    for name in logging.root.manager.loggerDict.keys():
        plugin_logger = logging.getLogger(name)
        if name in forbid_progagate:
            plugin_logger.propagate = False
        else:
            plugin_logger.propagate = True

    logger.remove()
    logger.configure(
        handlers=[
            {
                'sink': sys.stdout,
                'level': options.stdout_level,
                'format': options.file_options.format,
            }
        ]
    )

    configure_file_logging(options.files_config, options.file_options)


def configure_file_logging(
    files_config: LogFilesConfig,
    file_options: LogFileOptions
) -> None:
    base_options = dataclasses.asdict(file_options)
    directory: Path = base_options.pop('directory', Path('logs'))

    logger.add(
        directory.joinpath(files_config.error_log_file),
        level=files_config.error_log_level,
        backtrace=True,
        filter=lambda record: record['level'].no >= 30,
        diagnose=True,
        **base_options,
    )

    logger.add(
        file_options.directory.joinpath(files_config.access_log_file),
        level=files_config.access_log_level,
        filter=lambda record: record['level'].no <= 25,
        backtrace=False,
        diagnose=False,
        **base_options,
    )


def get_loguru_logger() -> 'Logger':
    return logger
