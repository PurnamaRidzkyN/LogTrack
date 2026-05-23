# ==========================================
# database/connection.py
# ==========================================

import sqlite3


DATABASE = "instance/auditflow.db"


def get_db_connection():

    conn = sqlite3.connect(
        DATABASE,
        timeout=30,
        isolation_level=None,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    return conn