

CONNECT_ARGS = {
    'check_same_thread': False
}

SQLITE3_PRAGMAS = {
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'cache_size': -64000,
    'foreign_keys': 1,
    'temp_store': 'MEMORY',
}