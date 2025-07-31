from __future__ import annotations

import atexit
import inspect
import logging
import sys
from typing import TYPE_CHECKING, Any

import structlog
from asgi_correlation_id import correlation_id
from loguru import Record
from loguru import logger as loguru_logger
from opentelemetry import trace

from . import const

if TYPE_CHECKING:
    from fastapi_template.core.settings import LoggerSettings


class LoguruIntercept(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame, depth = frame.f_back, depth + 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _add_correlation_id(_, __, ev: dict[str, Any]):
    if asgi_id := correlation_id.get():
        ev['correlation_id'] = asgi_id
    return ev


def _add_otel_id(_, __, ev: dict[str, Any]):
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.trace_id:
        ev['trace_id'] = f'{ctx.trace_id:032x}'
        ev['span_id'] = f'{ctx.span_id:016x}'
    return ev


def _flag_as_struct(_, __, ev):
    ev['_struct'] = True
    return ev


def _is_struct_log(record: Record) -> bool:
    if '_struct' in record:
        return record['_struct']
    return False


def _should_print(record: Record) -> bool:
    return not _is_struct_log(record)


def setup_logging(settings: LoggerSettings) -> None:
    logging.basicConfig(handlers=[LoguruIntercept()], level=settings.level, force=True)

    UVICORN_LOGGERS = ('uvicorn', 'uvicorn.access', 'uvicorn.error')

    for logger_name in UVICORN_LOGGERS:
        logging.getLogger(logger_name).handlers.clear()
        logging.getLogger(logger_name).propagate = True

    loguru_logger.remove()

    colorful_console = sys.stdout.isatty()
    loguru_logger.add(
        sys.stdout,
        level=settings.level,
        enqueue=True,
        serialize=False if colorful_console else settings.json_enabled,
        format=const.STDOUT_FORMAT,
        backtrace=False,
        diagnose=False,
        filter=_should_print,
    )

    logger_kwargs = {
        'rotation': settings.max_bytes,
        'retention': settings.retention,
        'compression': settings.compression,
        'enqueue': True,
        'serialize': True
    }

    def is_uvicorn_access(record: Record) -> bool:
        return record['name'] == 'uvicorn.access'

    loguru_logger.add(
        str(const.APP_LOG_FILE),
        level=settings.level,
        filter=lambda rec: not is_uvicorn_access(rec) and _is_struct_log(rec),
        **logger_kwargs,
    )

    loguru_logger.add(
        str(const.ERROR_LOG_FILE), level='ERROR', filter=_is_struct_log, **logger_kwargs
    )

    loguru_logger.add(
        str(const.ACCESS_LOG_FILE),
        level='INFO',
        filter=lambda rec: is_uvicorn_access(rec) and _is_struct_log(rec),
        **logger_kwargs,
    )

    atexit.register(loguru_logger.complete)

    structlog_processors = [
        _flag_as_struct,
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
    ]

    if settings.otel_enabled:
        structlog_processors.append(_add_otel_id)

    structlog_processors.extend(
        [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    )

    structlog.configure(
        processors=structlog_processors,
        wrapper_class=structlog.make_filtering_bound_logger(settings.level),
        logger_factory=lambda *a, **kw: loguru_logger.bind(_struct=True, **kw),
        cache_logger_on_first_use=True,
    )
