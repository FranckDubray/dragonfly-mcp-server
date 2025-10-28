
from __future__ import annotations
import time
import json as _json
import sqlite3
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv

# --- Timeouts helpers -------------------------------------------------------

def clamp_timeout(val: float) -> float:
    try:
        t = float(val)
    except Exception:
        t = 60.0
    if t <= 0:
        t = 60.0
    return max(0.1, min(t, 300.0))


def long_timeout_or_default(val):
    try:
        if val is None:
            return None
        v = float(val)
        if v <= 0:
            return None
        return min(v, 86400.0)
    except Exception:
        return None

# --- KV snapshot helpers ----------------------------------------------------

def read_pause_state(db_path: str, wn: str):
    paused_at = get_state_kv(db_path, wn, 'debug.paused_at') or ''
    next_node = get_state_kv(db_path, wn, 'debug.next_node') or ''
    cycle_id = get_state_kv(db_path, wn, 'debug.cycle_id') or ''
    last_step = get_state_kv(db_path, wn, 'debug.last_step') or ''
    last_step_node = ''
    try:
        if last_step:
            obj = _json.loads(last_step) if isinstance(last_step, str) else last_step
            last_step_node = (obj or {}).get('node') or ''
    except Exception:
        last_step_node = ''
    return paused_at, next_node, cycle_id, last_step_node


def read_step_snapshot(db_path: str, wn: str):
    call = get_state_kv(db_path, wn, 'py.last_call') or ''
    last_result_preview = get_state_kv(db_path, wn, 'py.last_result_preview') or ''
    phase = get_state_kv(db_path, wn, 'phase') or ''
    heartbeat = get_state_kv(db_path, wn, 'heartbeat') or ''
    last_error = get_state_kv(db_path, wn, 'last_error') or ''
    return call, last_result_preview, phase, heartbeat, last_error

# --- DB tail helpers --------------------------------------------------------

def db_max_rowid(dbp: str, wn: str, run_id: str) -> int:
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT COALESCE(MAX(rowid),0) FROM job_steps WHERE worker=? AND (run_id=? OR ?='')",
                (wn, run_id, run_id),
            )
            row = cur.fetchone()
            return int(row[0] or 0)
        finally:
            conn.close()
    except Exception:
        return 0


def db_rows_since(dbp: str, wn: str, run_id: str, last_rowid: int):
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT rowid, cycle_id, node, status, duration_ms, details_json, finished_at "
                "FROM job_steps WHERE worker=? AND (run_id=? OR ?='') AND rowid>? ORDER BY rowid ASC",
                (wn, run_id, run_id, int(last_rowid)),
            )
            return cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []


def db_recent_window(dbp: str, wn: str, run_id: str, window: int = 10):
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT rowid, cycle_id, node, status, duration_ms, details_json, finished_at "
                "FROM job_steps WHERE worker=? AND (run_id=? OR ?='') ORDER BY rowid DESC LIMIT ?",
                (wn, run_id, run_id, int(window)),
            )
            return cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []
