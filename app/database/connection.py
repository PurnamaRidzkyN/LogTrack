import sqlite3
from app.config import Config

def get_db_connection():
    conn = sqlite3.connect(
        Config.DATABASE_PATH,
        timeout=30,
        isolation_level=None,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    return conn