# SQLite helpers for orchestrator state (job_state_kv, job_steps, crash_logs)
# No ORM, minimal, fast. UTC microseconds timestamps.

import sqlite3
from pathlib import Path
from typing import Optional
from .utils import utcnow_str


def init_db(db_path: str) -> None:
    """Create tables if absent (idempotent)"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_state_kv (
                worker TEXT NOT NULL,
                skey TEXT NOT NULL,
                svalue TEXT,
                PRIMARY KEY (worker, skey)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                node TEXT NOT NULL,
                handler_kind TEXT,
                status TEXT NOT NULL CHECK(status IN ('running','succeeded','failed','skipped')),
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_ms INTEGER,
                edge_taken TEXT,
                details_json TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_steps_worker_cycle ON job_steps(worker, cycle_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_steps_node ON job_steps(node)")
        
        # NEW: Crash logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crash_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                node TEXT NOT NULL,
                crashed_at TEXT NOT NULL,
                error_message TEXT NOT NULL,
                error_type TEXT,
                error_code TEXT,
                worker_ctx_json TEXT,
                cycle_ctx_json TEXT,
                stack_trace TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crash_logs_worker ON crash_logs(worker)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crash_logs_cycle ON crash_logs(cycle_id)")
        
        conn.commit()
    finally:
        conn.close()

def get_state_kv(db_path: str, worker: str, key: str) -> Optional[str]:
    """Read state value (returns None if missing)"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?", (worker, key))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def set_state_kv(db_path: str, worker: str, key: str, value: str) -> None:
    """Write state value (upsert)"""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO job_state_kv (worker, skey, svalue) VALUES (?, ?, ?)",
            (worker, key, value)
        )
        conn.commit()
    finally:
        conn.close()

def get_phase(db_path: str, worker: str) -> Optional[str]:
    """Read current phase (starting|running|sleeping|canceling|canceled|failed|unknown)"""
    return get_state_kv(db_path, worker, 'phase')

def set_phase(db_path: str, worker: str, phase: str) -> None:
    """Set current phase"""
    set_state_kv(db_path, worker, 'phase', phase)

def heartbeat(db_path: str, worker: str) -> None:
    """Update heartbeat timestamp"""
    set_state_kv(db_path, worker, 'heartbeat', utcnow_str())
