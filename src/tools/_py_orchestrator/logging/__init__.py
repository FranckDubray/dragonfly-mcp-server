










# Minimal logging API: begin_step/end_step compatible with runner_parts.loop_core
import sqlite3
import json
from typing import Any, Dict
from ..utils.time import utcnow_str
from datetime import datetime
from ..db import get_state_kv


def _ensure_steps(conn: sqlite3.Connection):
    conn.execute(
        """
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
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_job_steps_worker ON job_steps(worker);")
    # New: composite index to speed filtering by current run
    conn.execute("CREATE INDEX IF NOT EXISTS idx_job_steps_worker_runid ON job_steps(worker, run_id);")


def begin_step(db_path: str, worker: str, cycle_id: str, node: str, *, handler_kind: str = "py_step") -> None:
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            _ensure_steps(conn)
            ts = utcnow_str()
            # Read current run_id from KV so rows are linked without trigger/migration
            try:
                run_id = get_state_kv(db_path, worker, 'run_id') or ''
            except Exception:
                run_id = ''
            conn.execute(
                "INSERT INTO job_steps (worker, cycle_id, node, status, handler_kind, duration_ms, started_at, finished_at, details_json, run_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (worker, cycle_id, node, 'running', handler_kind, 0, ts, None, None, run_id)
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def _parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def end_step(db_path: str, worker: str, cycle_id: str, node: str, status: str, finished_at: str, details: Dict[str, Any] | None) -> None:
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            _ensure_steps(conn)
            # Fetch the last running row for worker/node/cycle
            cur = conn.execute(
                "SELECT rowid, started_at FROM job_steps WHERE worker=? AND cycle_id=? AND node=? ORDER BY rowid DESC LIMIT 1",
                (worker, cycle_id, node)
            )
            row = cur.fetchone()
            if row:
                rid = row[0]
                started_at = row[1] or ''
                # Compute duration best-effort
                dur = 0
                try:
                    dt_s = _parse_dt(started_at)
                    dt_e = _parse_dt(finished_at)
                    if dt_s and dt_e:
                        dur = int((dt_e - dt_s).total_seconds() * 1000)
                        if dur < 0:
                            dur = 0
                except Exception:
                    dur = 0
                dj = None
                if details is not None:
                    try:
                        dj = json.dumps(details, ensure_ascii=False)
                    except Exception:
                        dj = json.dumps({"details": str(details)[:400]})
                conn.execute(
                    "UPDATE job_steps SET status=?, finished_at=?, duration_ms=?, details_json=? WHERE rowid=?",
                    (status, finished_at, dur, dj, rid)
                )
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
