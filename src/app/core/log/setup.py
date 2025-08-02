from __future__ import annotations

import atexit
import inspect
import logging
import sys
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from asgi_correlation_id import correlation_id
from loguru import logger as loguru_logger

from . import const

if TYPE_CHECKING:
    from loguru import Logger, Record


class LoguruIntercept(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 2
        while frame and (frame.f_code.co_filename == logging.__file__):
            frame, depth = frame.f_back, depth + 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _add_request_id(record: Record) -> None:
    request_id = correlation_id.get() or 'unknown'
    record['extra']['request_id'] = request_id


def create_file_logger(
    name: str,
    level: str,
    *,
    logger_type: str,
    diagnose: bool = False,
    backtrace: bool = False,
) -> None:
    file_pattern = '_{time:YYYY-MM-DD}.log'

    path = const.LOGS_DIR / name
    path.mkdir(exist_ok=True)

    def _filter(record: Record) -> bool:
        return record['extra'].get('logger_type', '') == logger_type

    filename = name + file_pattern

    loguru_logger.add(
        path / filename,
        level=level,
        serialize=True,
        enqueue=True,
        filter=_filter,
        backtrace=backtrace,
        diagnose=diagnose,
        **const.FILE_LOGGING_OPTIONS,
    )


def configure_logger(root_log_level: str) -> None:
    intercept_handler = LoguruIntercept()

    for logger_name in const.FRAMEWOR_LOGGERS:
        framework_logger = logging.getLogger(logger_name)
        framework_logger.handlers = [intercept_handler]
        framework_logger.setLevel(root_log_level)
        framework_logger.propagate = False

    logging.basicConfig(handlers=[intercept_handler], level=root_log_level, force=True)

    loguru_logger.remove()
    loguru_logger.configure(
        handlers=[
            {
                'sink': sys.stdout,
                'level': root_log_level,
                'format': const.STDOUT_FORMAT,
                'enqueue': True,
            }
        ],
        patcher=_add_request_id,
    )


class FileLoggerType(StrEnum):
    APP = 'app'
    ERROR = 'error'
    ACCESS = 'access'


def configure_file_loggers(
    *,
    app_level: str = 'INFO',
    error_level: str = 'ERROR',
    access_level: str = 'INFO',
) -> None:
    create_file_logger(
        'app',
        app_level,
        logger_type=FileLoggerType.APP,
        diagnose=True,
        backtrace=True,
    )

    create_file_logger(
        'errors.log',
        error_level,
        logger_type=FileLoggerType.ERROR,
        diagnose=True,
        backtrace=True,
    )

    create_file_logger(
        'access.log',
        access_level,
        logger_type=FileLoggerType.ACCESS,
        diagnose=False,
        backtrace=False,
    )

    atexit.register(loguru_logger.remove)


def get_json_logger(
    logger_type: FileLoggerType, base_context: dict[str, Any] | None = None
) -> Logger:
    context = base_context or {}
    context['logger_type'] = logger_type.value

    return loguru_logger.bind(**context)
