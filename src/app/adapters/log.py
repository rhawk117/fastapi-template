







from __future__ import annotations

import atexit
import logging
import sys
from typing import TYPE_CHECKING, NamedTuple

from asgi_correlation_id import correlation_id
from loguru import logger as root_loguru_logger

from app.core import path_utils, settings
from app.core.singleton import SingletonMeta

if TYPE_CHECKING:
    from loguru import Logger, Record


class InterceptHandler(logging.Handler):
    """
    Allows standard library loggers to be intercepted by loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = root_loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        root_loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def get_loguru_logger() -> 'Logger':
    return root_loguru_logger


def inject_asgi_correlation_id(record: 'Record') -> bool:
    record['extra']['correlation_id'] = correlation_id.get() or 'N/A'
    return True



class _JsonLogBind(NamedTuple):
    logger: 'Logger'
    sink_id: int

class JsonLogAdapter(metaclass=SingletonMeta):
    _sink_binds: dict[str, _JsonLogBind] = {}


    def _make_sink(self, logger_name: str, config: settings.LoggerConfig) -> str:
        directory = path_utils.abs_root_path(config.DIRECTORY) / logger_name
        directory.mkdir(parents=True, exist_ok=True)
        pattern = directory / f'{logger_name}_%Y-%m-%d.log'
        return str(pattern)

    def register(self, name: str, level: str) -> None:
        """
        Registers a new JSON logger with the specified name and level.

        Parameters
        ----------
        name : str
            The name of the logger.
        level : str
            The logging level for the logger.

        Returns
        -------
        Logger
            The configured `loguru` JSON logger.
        """
        if name in self._sink_binds:
            return

        config = settings.get_app_settings().logger
        loguru_logger = get_loguru_logger()
        sink = self._make_sink(name, config)

        bind = loguru_logger.bind(component=name)
        sink_id = loguru_logger.add(
            sink,
            level=level,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            rotation=f'{config.ROTATION_MB} MB',
            retention=f'{config.RETENTION_DAYS} days',
            compression=config.COMPRESSION,
            serialize=True,
            filter=inject_asgi_correlation_id,
        )
        self._sink_binds[name] = _JsonLogBind(logger=bind, sink_id=sink_id)

    def get_logger(self, name: str) -> 'Logger':
        """
        Retrieves a previously registered JSON logger by its name.

        Parameters
        ----------
        name : str
            The name of the logger to retrieve.

        Returns
        -------
        Logger | None
            The `loguru` JSON logger if found, otherwise `None`.
        """
        if not (bind := self._sink_binds.get(name)):
            raise ValueError(f'Logger with name {name} is not registered.')
        return bind.logger

    def dispose(self) -> None:
        """
        Disposes of all registered JSON loggers, removing their sinks from the
        `loguru` logger.
        """
        loguru_logger = get_loguru_logger()
        for bind in self._sink_binds.values():
            loguru_logger.remove(bind.sink_id)
        self._sink_binds.clear()

    def make(self, logger: str, level: str) -> 'Logger':
        """
        Convenience method to register and retrieve a JSON logger in one step.

        Parameters
        ----------
        logger : str
            The name of the logger.
        level : str
            The logging level for the logger.

        Returns
        -------
        Logger
            The configured `loguru` JSON logger.
        """
        self.register(logger, level)
        return self.get_logger(logger)


def setup_logging() -> None:
    """
    Sets up the logging by loading the `LogSettings` from the config.toml file

    Side effects:
        - Adds an `InterceptHandler` to the root logger.
        - Configures the `loguru` logger to log to stdout with specified levels and
        formats.
        -If `json_loggers` are specified in the settings, it adds them to the
        `_LOG_REGISTRY` constant
        - Registers a cleanup function to dispose of the `_LOG_REGISTRY` on exit.
    """

    config = settings.get_app_settings()

    loguru_logger = get_loguru_logger()
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    noisey_loggers = ('uvicorn.error', 'uvicorn.access')
    for logger_name in noisey_loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers = [InterceptHandler()]
        logger.propagate = False

    loguru_logger.remove()
    loguru_logger.add(
        sys.stdout,
        level=config.logger.LEVEL,
        colorize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=config.logger.stdout_format,
        filter=inject_asgi_correlation_id,
    )

    atexit.register(JsonLogAdapter().dispose)

def get_json_adapter() -> JsonLogAdapter:
    '''
    Convenience function to get the singleton instance of `JsonLogAdapter`.

    Returns
    -------
    JsonLogAdapter
    '''
    return JsonLogAdapter()