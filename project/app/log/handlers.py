from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger


class LoguruInterceptor(logging.Handler):
    def __init__(self, loguru_logger: Logger) -> None:
        """
        Initialize the LoguruInterceptor with a Loguru logger.

        Parameters
        ----------
        loguru_logger : Logger
            The Loguru logger instance to intercept log records.
        """
        super().__init__()
        self.loguru_logger = loguru_logger

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the Loguru logger.

        Parameters
        ----------
        record : logging.LogRecord
        """
        try:
            level = self.loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        self.loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
