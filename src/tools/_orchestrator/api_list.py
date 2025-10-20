# List workers operation (module <7KB)

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

from .api_spawn import SQLITE_DIR


def _read_state(db_path: str, worker: str, key: str) -> str:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?", (worker, key))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""


def _read_last_step_time(db_path: str, worker: str) -> str:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(MAX(finished_at), MAX(started_at))
            FROM job_steps
            WHERE worker=?
            """,
            (worker,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row and row[0] else ""
    except Exception:
        return ""


def list_workers() -> Dict[str, Any]:
    """List all workers (sqlite3/worker_*.db) with compact status.
    Returns: {accepted: true, status: ok, workers: [ {...} ]}
    """
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    workers: List[Dict[str, Any]] = []
    for entry in os.listdir(SQLITE_DIR):
        if not entry.startswith("worker_") or not entry.endswith(".db"):
            continue
        db_path = str(Path(SQLITE_DIR) / entry)
        # Derive worker name from filename
        wname = entry[:-3]  # remove .db
        wname = wname.replace("worker_", "", 1)
        # Read compact state
        phase = _read_state(db_path, wname, 'phase') or 'unknown'
        pid = _read_state(db_path, wname, 'pid')
        heartbeat = _read_state(db_path, wname, 'heartbeat')
        process_uid = _read_state(db_path, wname, 'process_uid')
        process_version = _read_state(db_path, wname, 'process_version')
        last_error = _read_state(db_path, wname, 'last_error')
        last_step_at = _read_last_step_time(db_path, wname)
        workers.append({
            'worker_name': wname,
            'status': phase,
            'pid': int(pid) if pid.isdigit() else None,
            'heartbeat': heartbeat,
            'last_step_at': last_step_at,
            'process_uid': process_uid,
            'process_version': process_version,
            'db_path': db_path,
            'last_error': (last_error[:200] if last_error else None)
        })
    return {"accepted": True, "status": "ok", "workers": workers}
