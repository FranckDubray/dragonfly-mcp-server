
from __future__ import annotations
from typing import Any, Dict, List
import time
import json as _json
import sqlite3

from .api_spawn import db_path_for_worker
from .db import get_state_kv


def _long_timeout_or_default(val):
    try:
        if val is None:
            return None
        v = float(val)
        if v <= 0:
            return None
        return min(v, 86400.0)
    except Exception:
        return None


def _db_max_rowid(dbp: str, wn: str, run_id: str) -> int:
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


def _db_rows_since(dbp: str, wn: str, run_id: str, last_rowid: int):
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


def _db_recent_window(dbp: str, wn: str, run_id: str, window: int = 10):
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


def observe_tool(params: dict) -> dict:
    """Passive observation window. Does NOT enable debug nor step/continue.
    Returns a single JSON response with events captured in the window.
    """
    wn = str((params or {}).get('worker_name') or '').strip()
    if not wn:
        return {"accepted": False, "status": "error", "message": "worker_name required", "truncated": False}

    db_path = db_path_for_worker(wn)
    obs_req = (params or {}).get('observe') or {}

    timeout_sec = _long_timeout_or_default(obs_req.get('timeout_sec'))
    deadline = (time.time() + timeout_sec) if (timeout_sec is not None) else None

    events: List[Dict[str, Any]] = []
    tick = 0.2
    max_events = int(obs_req.get('max_events') or 0)  # 0 = unlimited

    run_id = get_state_kv(db_path, wn, 'run_id') or ''
    last_rowid = _db_max_rowid(db_path, wn, run_id)
    # Track recent updates: rowid -> signature(status, finished_at, duration_ms, details_json_hash)
    seen_sig = {}

    while True:
        if deadline is not None and time.time() > deadline:
            return {"accepted": True, "status": "timeout", "events": events, "count": len(events)}

        phase = get_state_kv(db_path, wn, 'phase') or ''
        if phase in {'completed', 'failed', 'canceled'}:
            # Emit a terminal snapshot chunk (without forcing any debug state)
            call = ''
            lrp = ''
            try:
                # Optional: recent last call/preview from KV (best-effort)
                call = get_state_kv(db_path, wn, 'py.last_call') or ''
                lrp = get_state_kv(db_path, wn, 'py.last_result_preview') or ''
            except Exception:
                pass
            events.append({
                'chunk_type': ('error' if (phase == 'failed') else 'step'),
                'node_executed': '',
                'node_next': '',
                'io': {'in': call, 'out_preview': lrp},
                'error': ({'message': get_state_kv(db_path, wn, 'last_error') or ''} if phase == 'failed' else None),
                'phase': phase,
                'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                'cycle_id': get_state_kv(db_path, wn, 'debug.cycle_id') or '',
                'terminal': True,
            })
            return {"accepted": True, "status": phase, "events": events, "count": len(events)}

        # New inserts since last_rowid
        rows = _db_rows_since(db_path, wn, run_id, last_rowid)
        if rows:
            for rid, cycle_id, node, status, dur, dj, fin in rows:
                call = {}
                lrp = ''
                try:
                    if dj:
                        obj = _json.loads(dj)
                        if isinstance(obj, dict):
                            call = obj.get('call') or {}
                            lrp_val = obj.get('last_result_preview')
                            if lrp_val is not None:
                                lrp = lrp_val if isinstance(lrp_val, str) else str(lrp_val)
                except Exception:
                    pass
                events.append({
                    'chunk_type': ('error' if str(status).lower()=='failed' else 'step'),
                    'node_executed': node,
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(db_path, wn, 'last_error') or '')} if str(status).lower()=='failed' else None),
                    'phase': get_state_kv(db_path, wn, 'phase') or '',
                    'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                })
                sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
                seen_sig[int(rid)] = sig
                last_rowid = int(rid)
                if max_events and len(events) >= max_events:
                    return {"accepted": True, "status": "ok", "events": events, "count": len(events), "truncated": True}
        else:
            time.sleep(tick)

        # Updates in recent window
        recent = _db_recent_window(db_path, wn, run_id, window=10)
        for rid, cycle_id, node, status, dur, dj, fin in reversed(recent):
            rid_i = int(rid)
            cur_sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
            prev_sig = seen_sig.get(rid_i)
            if prev_sig is None:
                seen_sig[rid_i] = cur_sig
                continue
            if cur_sig != prev_sig:
                call = {}
                lrp = ''
                try:
                    if dj:
                        obj = _json.loads(dj)
                        if isinstance(obj, dict):
                            call = obj.get('call') or {}
                            lrp_val = obj.get('last_result_preview')
                            if lrp_val is not None:
                                lrp = lrp_val if isinstance(lrp_val, str) else str(lrp_val)
                except Exception:
                    pass
                events.append({
                    'chunk_type': ('error' if str(status).lower()=='failed' else 'step'),
                    'node_executed': node,
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(db_path, wn, 'last_error') or '')} if str(status).lower()=='failed' else None),
                    'phase': get_state_kv(db_path, wn, 'phase') or '',
                    'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                    'updated': True,
                })
                seen_sig[rid_i] = cur_sig
                if max_events and len(events) >= max_events:
                    return {"accepted": True, "status": "ok", "events": events, "count": len(events), "truncated": True}
