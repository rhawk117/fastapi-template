import logging
import sys


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
    from .json_logging import setup_json_logging
    from .settings import log_settings
    from .utils import InterceptHandler, get_loguru_logger, inject_asgi_correlation_id

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
        level=log_settings.stdout_level,
        colorize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=log_settings.stdout_format,
        filter=inject_asgi_correlation_id,
    )

    setup_json_logging()
