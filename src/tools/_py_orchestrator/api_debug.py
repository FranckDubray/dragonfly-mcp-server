
from .validators import validate_params
from .._orchestrator.api_debug import debug_control as json_debug_control
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv
import time
import json as _json
import sqlite3


def _clamp_timeout(val: float) -> float:
    try:
        t = float(val)
    except Exception:
        t = 60.0  # default now 60s
    # allow long waits up to 300s for LLM/worker calls; min 0.1s
    if t <= 0:
        t = 60.0
    return max(0.1, min(t, 300.0))


def _long_timeout_or_default(val):
    """Observation stream timeout policy.
    - None or <=0 means: no server-side deadline (client controls the connection lifetime).
    - Positive values: seconds until server returns.
    - Hard safety cap still enforced at 24h if a huge value is provided.
    """
    try:
        if val is None:
            return None  # infinite by default
        v = float(val)
        if v <= 0:
            return None
        return min(v, 86400.0)
    except Exception:
        return None


def _read_pause_state(db_path: str, wn: str):
    paused_at = get_state_kv(db_path, wn, 'debug.paused_at') or ''
    next_node = get_state_kv(db_path, wn, 'debug.next_node') or ''
    cycle_id = get_state_kv(db_path, wn, 'debug.cycle_id') or ''
    last_step = get_state_kv(db_path, wn, 'debug.last_step') or ''
    # last_step is a compact JSON string like {"node":"SUB::STEP","type":"py_step"}
    last_step_node = ''
    try:
        if last_step:
            obj = _json.loads(last_step) if isinstance(last_step, str) else last_step
            last_step_node = (obj or {}).get('node') or ''
    except Exception:
        last_step_node = ''
    return paused_at, next_node, cycle_id, last_step_node


def _read_step_snapshot(db_path: str, wn: str):
    call = get_state_kv(db_path, wn, 'py.last_call') or ''
    last_result_preview = get_state_kv(db_path, wn, 'py.last_result_preview') or ''
    phase = get_state_kv(db_path, wn, 'phase') or ''
    heartbeat = get_state_kv(db_path, wn, 'heartbeat') or ''
    last_error = get_state_kv(db_path, wn, 'last_error') or ''
    return call, last_result_preview, phase, heartbeat, last_error


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


def _stream(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'debug'})
    wn = p['worker_name']
    db_path = db_path_for_worker(wn)

    # Enable debug step mode immediately
    json_debug_control({'operation': 'debug', 'worker_name': wn, 'debug': {'action': 'enable_now'}})

    # Streaming loop: DB tail (insert + update) with auto-step to next boundaries if paused
    dbg_req = (params or {}).get('debug') or {}
    timeout_sec = _long_timeout_or_default(dbg_req.get('timeout_sec'))
    deadline = (time.time() + timeout_sec) if (timeout_sec is not None) else None

    set_state_kv(db_path, wn, 'debug.mode', 'step')

    events = []
    tick = 0.2
    max_events = int(dbg_req.get('max_events') or 0)  # 0 = unlimited

    run_id = get_state_kv(db_path, wn, 'run_id') or ''
    last_rowid = _db_max_rowid(db_path, wn, run_id)
    # Track recent updates: rowid -> signature(status, finished_at, duration_ms, details_json_hash)
    seen_sig = {}

    while True:
        # Timeout / terminal checks
        if deadline is not None and time.time() > deadline:
            return {'accepted': True, 'status': 'timeout', 'events': events, 'count': len(events)}
        phase = get_state_kv(db_path, wn, 'phase') or ''
        if phase in {'completed', 'failed', 'canceled'}:
            call, lrp, ph, hb, last_err = _read_step_snapshot(db_path, wn)
            if call or lrp or last_err:
                events.append({
                    'chunk_type': ('error' if (phase == 'failed' or last_err) else 'step'),
                    'node_executed': '',
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': last_err} if last_err else None),
                    'phase': ph or phase,
                    'heartbeat': hb,
                    'cycle_id': get_state_kv(db_path, wn, 'debug.cycle_id') or '',
                    'terminal': True,
                })
            return {'accepted': True, 'status': phase, 'events': events, 'count': len(events)}

        # 1) New inserts since last_rowid
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
                # seed signature cache
                sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
                seen_sig[int(rid)] = sig
                last_rowid = int(rid)
                if max_events and len(events) >= max_events:
                    return {'accepted': True, 'status': 'ok', 'events': events, 'count': len(events), 'truncated': True}
                # ask runner to proceed one boundary (cooperative)
                try:
                    dbg_enabled = (get_state_kv(db_path, wn, 'debug.enabled') == 'true')
                    if dbg_enabled:
                        json_debug_control({'operation': 'debug', 'worker_name': wn, 'debug': {'action': 'step', 'timeout_sec': 0.1}})
                except Exception:
                    pass
        else:
            time.sleep(tick)

        # 2) Updates in recent window (running -> succeeded/failed)
        recent = _db_recent_window(db_path, wn, run_id, window=10)
        for rid, cycle_id, node, status, dur, dj, fin in reversed(recent):
            rid_i = int(rid)
            cur_sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
            prev_sig = seen_sig.get(rid_i)
            if prev_sig is None:
                # unseen in window; skip (insert case handled above)
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
                    return {'accepted': True, 'status': 'ok', 'events': events, 'count': len(events), 'truncated': True}


def debug_control(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'debug'})

    # Streaming/Observation mode (long-lived, auto-step, chunked events in one response)
    dbg_req = (params or {}).get('debug') or {}
    action = str(dbg_req.get('action') or '').lower()
    if action == 'stream':
        return _stream(params)

    # Fast-path checks (avoid useless waits)
    db_path = db_path_for_worker(p['worker_name'])

    # Terminal phases: do not attempt debug changes
    try:
        phase = get_state_kv(db_path, p['worker_name'], 'phase') or ''
        if phase in {'completed', 'failed', 'canceled'}:
            return {'accepted': False, 'status': 'terminal', 'message': f'Worker is in terminal phase: {phase}'}
    except Exception:
        pass

    # If already enabled, acknowledge immediately for enable/enable_now
    if action in {'enable', 'enable_now'}:
        try:
            dbg_enabled = (get_state_kv(db_path, p['worker_name'], 'debug.enabled') == 'true')
            if dbg_enabled:
                return {'accepted': True, 'status': 'already_enabled'}
        except Exception:
            pass

    # Forward to JSON orchestrator debug control (same DB keys/protocol)
    res = json_debug_control({'operation':'debug','worker_name': p['worker_name'], 'debug': dbg_req})

    # Blocking ACK: only for actions that cause movement (step/continue/run_until)
    try:
        timeout = _clamp_timeout(dbg_req.get('timeout_sec', 60.0))
        if action in {'step', 'continue', 'run_until'} and timeout > 0:
            deadline = time.time() + timeout
            tick = 0.1 if timeout <= 2.0 else 0.2
            while time.time() < deadline:
                paused_at = get_state_kv(db_path, p['worker_name'], 'debug.paused_at') or ''
                next_node = get_state_kv(db_path, p['worker_name'], 'debug.next_node') or ''
                if paused_at or next_node:
                    cycle_id = get_state_kv(db_path, p['worker_name'], 'debug.cycle_id') or ''
                    paused_out = paused_at or next_node
                    return {'accepted': True, 'status': 'paused', 'paused_at': paused_out, 'cycle_id': cycle_id}
                phase = get_state_kv(db_path, p['worker_name'], 'phase') or ''
                if phase in {'completed','failed','canceled'}:
                    return {'accepted': True, 'status': phase}
                time.sleep(tick)
    except Exception:
        pass
    return res
