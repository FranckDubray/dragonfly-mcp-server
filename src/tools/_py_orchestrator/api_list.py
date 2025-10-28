
# List workers (autonomous; no dependency on old JSON orchestrator)
from __future__ import annotations
from pathlib import Path
import sqlite3
from typing import List, Dict, Any

from .api_common import SQLITE_DIR


def _read_kv(conn: sqlite3.Connection, key: str, worker: str) -> str:
    try:
        cur = conn.execute(
            "SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?",
            (worker, key),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else ""
    except Exception:
        return ""


def _last_step_ts(conn: sqlite3.Connection, worker: str) -> str:
    try:
        cur = conn.execute(
            "SELECT COALESCE(finished_at, started_at) FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1",
            (worker,),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else ""
    except Exception:
        return ""


def list_workers() -> Dict[str, Any]:
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    items: List[Dict[str, Any]] = []

    for dbp in sorted(Path(SQLITE_DIR).glob("worker_*.db")):
        try:
            worker_name = dbp.stem.replace("worker_", "", 1)
            conn = sqlite3.connect(str(dbp), timeout=2.0)
            try:
                phase = _read_kv(conn, "phase", worker_name) or "unknown"
                pid = _read_kv(conn, "pid", worker_name)
                hb = _read_kv(conn, "heartbeat", worker_name)
                process_uid = _read_kv(conn, "process_uid", worker_name)
                last_err = _read_kv(conn, "last_error", worker_name) or None
                last_step_at = _last_step_ts(conn, worker_name)
            finally:
                conn.close()
            items.append({
                "worker_name": worker_name,
                "status": phase or "unknown",
                "pid": (int(pid) if pid and pid.isdigit() else None),
                "heartbeat": hb,
                "last_step_at": last_step_at,
                "process_uid": process_uid or "",
                "process_version": "",
                "db_path": str(dbp.resolve()),
                "last_error": last_err,
            })
        except Exception:
            # Skip unreadable DBs
            continue

    return {"accepted": True, "status": "ok", "workers": items}
