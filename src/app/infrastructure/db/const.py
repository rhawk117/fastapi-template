CONNECT_ARGS = {
    'check_same_thread': False,
}

DB_DRIVER_NAME = 'sqlite+aiosqlite'

PRAGMAS = {
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'cache_size': -64000,
    'foreign_keys': 1,
    'temp_store': 'MEMORY',
}
