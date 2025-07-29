from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final

CONNECT_ARGS: Final[dict[str, Any]] = {
    'check_same_thread': False,
}

DRIVER_NAME: Final[str] = 'sqlite+aiosqlite'

SQLITE_PRAGMAS: Final[dict[str, Any]] = {
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'cache_size': -64000,
    'foreign_keys': 1,
    'temp_store': 'MEMORY',
}
