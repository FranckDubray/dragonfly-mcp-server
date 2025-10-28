
# Autonomous SQLite helpers for Python Orchestrator
import sqlite3
from typing import Optional
from .utils.time import utcnow_str

SCHEMA_STATE = """
CREATE TABLE IF NOT EXISTS job_state_kv (
  worker TEXT NOT NULL,
  skey   TEXT NOT NULL,
  svalue TEXT,
  PRIMARY KEY(worker, skey)
);
"""

# Minimal job_steps schema (logging layer may enrich/migrate later)
SCHEMA_STEPS = """
CREATE TABLE IF NOT EXISTS job_steps (
  worker TEXT,
  cycle_id TEXT,
  node TEXT,
  status TEXT,
  handler_kind TEXT,
  duration_ms INTEGER,
  started_at TEXT,
  finished_at TEXT,
  details_json TEXT,
  run_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_steps_worker ON job_steps(worker);
"""


def init_db(db_path: str) -> None:
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.executescript(SCHEMA_STATE)
            conn.executescript(SCHEMA_STEPS)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def get_state_kv(db_path: str, worker: str, key: str) -> Optional[str]:
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?",
                (worker, key)
            )
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None
        finally:
            conn.close()
    except Exception:
        return None


def set_state_kv(db_path: str, worker: str, key: str, value: str) -> None:
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            conn.execute(
                "INSERT INTO job_state_kv(worker,skey,svalue) VALUES(?,?,?) "
                "ON CONFLICT(worker,skey) DO UPDATE SET svalue=excluded.svalue",
                (worker, key, value)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def get_phase(db_path: str, worker: str) -> str:
    v = get_state_kv(db_path, worker, 'phase')
    return v or ''


def set_phase(db_path: str, worker: str, phase: str) -> None:
    set_state_kv(db_path, worker, 'phase', str(phase))


def heartbeat(db_path: str, worker: str) -> None:
    set_state_kv(db_path, worker, 'heartbeat', utcnow_str())

__all__ = ['init_db','get_state_kv','set_state_kv','get_phase','set_phase','heartbeat']
