
import sqlite3
from typing import Any
from ..utils.time import utcnow_str

# Best-effort crash logging compatible with existing schema (crash_logs)
# Schema (expected): id INTEGER PK, ts TEXT, worker TEXT, cycle_id TEXT, node TEXT, message TEXT

def _ensure_table(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS crash_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT,
          worker TEXT,
          cycle_id TEXT,
          node TEXT,
          message TEXT
        )
        """
    )


def log_crash(db_path: str, worker: str, *, cycle_id: str, node: str, error: Exception, worker_ctx: Any = None, cycle_ctx: Any = None) -> None:
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            _ensure_table(conn)
            ts = utcnow_str()
            msg = str(error)[:400] if error else ''
            conn.execute(
                "INSERT INTO crash_logs (ts, worker, cycle_id, node, message) VALUES (?, ?, ?, ?, ?)",
                (ts, worker, cycle_id, node, msg)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Best effort: never crash caller
        pass
