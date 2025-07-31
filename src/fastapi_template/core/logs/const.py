from pathlib import Path

APP_ROOT = Path(__file__).parent.parent.parent.resolve()

LOGS_DIR = APP_ROOT / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


APP_LOG_FILE: Path = LOGS_DIR / 'app_{time:YYYY-MM-DD_HH-mm-ss}_{process}.log'
ERROR_LOG_FILE: Path = LOGS_DIR / 'errors_{time:YYYY-MM-DD_HH-mm-ss}_{process}.log'
ACCESS_LOG_FILE: Path = LOGS_DIR / 'access_{time:YYYY-MM-DD_HH-mm-ss}_{process}.log'

STDOUT_FORMAT = (
    '<green>{time:YYYY‑MM‑DD HH:mm:ss.SSS}</green> | '
    '<lvl>{level:<8}</lvl> | '
    '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> → '
    '<lvl>{message}</lvl>'
)

