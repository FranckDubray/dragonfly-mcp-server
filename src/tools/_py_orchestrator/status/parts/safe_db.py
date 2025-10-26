
import sqlite3
from typing import Callable, Any


def safe_query(db_path: str, query: str, params: tuple = (), row_handler: Callable[[sqlite3.Row], Any] | None = None):
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            if row_handler:
                return [row_handler(r) for r in rows]
            return rows
        finally:
            conn.close()
    except Exception:
        return []
