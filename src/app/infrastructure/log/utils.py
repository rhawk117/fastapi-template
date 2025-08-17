import logging
from typing import TYPE_CHECKING

from asgi_correlation_id import correlation_id
from loguru import logger as loguru_logger

if TYPE_CHECKING:
    from loguru import Logger, Record


class InterceptHandler(logging.Handler):
    """
    Allows standard library loggers to be intercepted by loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def get_loguru_logger() -> Logger:
    return loguru_logger


def inject_asgi_correlation_id(record: Record) -> bool:
    record['extra']['correlation_id'] = correlation_id.get() or 'N/A'
    return True
