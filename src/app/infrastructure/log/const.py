from pathlib import Path

_APP_ROOT = Path(__file__).parent.parent.parent.resolve()


LOGS_DIR = _APP_ROOT / 'logs'
STDOUT_FORMAT = (
    '<cyan>{name}</> - '
    '<green>{time:YYYY‑MM‑DD HH:mm:ss.SSS}</> | '
    '<blue>{request_id}</> |'
    '<lvl>{level:<8}</> | '
    '<lvl>{message}</> (<gray>{function}:{line}</>)'
)

FRAMEWOR_LOGGERS = frozenset({'uvicorn', 'uvicorn.access', 'fastapi', 'starlette'})


FILE_LOGGING_OPTIONS = {
    'max_bytes': '10 MB',
    'rotation': '00:00',
    'compression': 'gz',
    'retention': '7 days',
    'serialize': True,
    'enqueue': True,
}
