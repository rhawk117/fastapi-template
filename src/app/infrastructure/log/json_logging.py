import atexit
import functools
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from core import path_utils

from .settings import log_settings
from .utils import get_loguru_logger, inject_asgi_correlation_id

if TYPE_CHECKING:
    from loguru import Logger


def _get_file_logger_dir(logger_name: str) -> Path:
    """
    Creates a directory for the logger if it does not exist.

    Parameters
    ----------
    logger_name : str

    Returns
    -------
    Path
    """
    app_root = path_utils.get_app_root()

    logger_dir = app_root.joinpath(log_settings.directory, logger_name)

    logger_dir.mkdir(parents=True, exist_ok=True)

    return logger_dir


def _file_log_pattern(directory: Path, logger_name: str) -> str:
    timestamp = '{time:YYYY-MM-DD}'
    return str(directory.joinpath(f'{logger_name}_{timestamp}.log'))


class JsonLoggerHook:
    """
    Setups a binded logger with a file sink for JSON formatted logs,
    and has a `close()` method to dispose of it on shutdown.

    _not a dataclass since your technically not supposed to import
    "Logger" from loguru directly and can use future annotations
    to import without issue_

    """

    __slots__ = ('_bind', '_sink_id')

    def __init__(self, name: str, level: str) -> None:
        directory = _get_file_logger_dir(name)
        sink = _file_log_pattern(directory, name)
        self._bind: Logger = get_loguru_logger().bind(
            component=name,
        )
        self._sink_id: int = get_loguru_logger().add(
            sink,
            level=level,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            rotation=f'{log_settings.rotation_mb} MB',
            retention=f'{log_settings.retention_days} days',
            compression=log_settings.compression,
            serialize=True,
            filter=inject_asgi_correlation_id,
        )

    @property
    def logger(self) -> Logger:
        return self._bind

    def close(self) -> None:
        try:
            if hasattr(self, '_sink_id'):
                self._bind.remove(self._sink_id)
                delattr(self, '_sink_id')
        except Exception:
            pass

    async def __call__(self, level: str, message: str, *args, **kwargs) -> None:
        """
        Asynchronously logs a message with the specified level.

        Parameters
        ----------
        level : str
            The logging level.
        *args : Any
            Positional arguments to log.
        **kwargs : Any
            Keyword arguments to log.
        """
        self._bind.log(level, message, *args, **kwargs)


@dataclass(frozen=True, slots=True)
class _JsonLoggerRegistry:
    _binds: dict[str, JsonLoggerHook] = field(default_factory=dict, init=False)

    def register(self, name: str, level: str) -> None:
        """
        Adds a new logger to the registry.

        Parameters
        ----------
        name : str
            The name of the logger.
        level : str
            The logging level for the logger.
        """
        if name in self._binds:
            raise RuntimeError(f'Logger with name {name} is already registered.')

        context = JsonLoggerHook(name=name, level=level)
        self._binds[name] = context

    def dispose(self) -> None:
        """
        Closes all loggers in the registry.
        """
        for logger in self._binds.values():
            logger.close()
        self._binds.clear()

    def get(self, name: str) -> JsonLoggerHook:
        """
        Retrieves a logger by name from the registry.
        Parameters
        ----------
        name : str

        Returns
        -------
        Logger

        Raises
        ------
        KeyError
            If the logger with the specified name does not exist.
        """
        return self._binds[name]


@functools.lru_cache(maxsize=1)
def get_json_registry() -> _JsonLoggerRegistry:
    """
    Retrieves the singleton instance of the JsonLoggerRegistry.

    Returns
    -------
    _JsonLoggerRegistry
        The singleton instance of the JsonLoggerRegistry.
    """
    return _JsonLoggerRegistry()


def setup_json_logging() -> None:
    """
    Sets up the JSON loggers based on the configuration in
    `log_settings`.
    """
    if not log_settings.json_loggers:
        return
    registry = get_json_registry()
    for options in log_settings.json_loggers:
        registry.register(name=options.name, level=options.level)

    atexit.register(registry.dispose)


def create_json_logger(name: str, level: str = 'INFO') -> Logger:
    """
    Creates a JSON logger with the specified name and level.

    Parameters
    ----------
    name : str
        The name of the logger.
    level : str, optional
        The logging level for the logger (default is 'INFO').

    Returns
    -------
    JsonLoggerHook
        The created JSON logger.
    """
    registry = get_json_registry()
    registry.register(name, level)
    return registry.get(name).logger


def get_json_logger(name: str) -> Logger:
    """
    Retrieves a JSON logger by name.

    Parameters
    ----------
    name : str
        The name of the logger.

    Returns
    -------
    Logger
        The JSON logger with the specified name.

    Raises
    ------
    KeyError
        If the logger with the specified name does not exist.
    """
    return get_json_registry().get(name).logger
