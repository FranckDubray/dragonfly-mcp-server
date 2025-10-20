












# Status & Debug operations (module <7KB)

import json
import time
import uuid
import sqlite3
from pathlib import Path
from typing import Any, Dict
from datetime import datetime, timedelta, timezone

from .validators import validate_params
from .api_common import db_path_for_worker, compact_errors_for_status, debug_status_block
from .db import get_state_kv, set_state_kv, get_phase


def _compute_metrics_window(db_path: str, worker: str, minutes: int = 60) -> Dict[str, Any]:
    """Compute compact metrics over the last N minutes from job_steps.
    Returns a tiny dict (counts only), safe for UI/LLM (no large payloads).
    """
    if minutes <= 0:
        minutes = 60
    cutoff_dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    cutoff = cutoff_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    nodes_executed = 0
    sum_duration = 0
    count_duration = 0
    errors = {"io": 0, "validation": 0, "permission": 0, "timeout": 0}
    retries_attempts = 0
    nodes_with_retries = set()
    llm_tokens = 0

    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            cur = conn.execute(
                """
                SELECT node, status, duration_ms, details_json
                FROM job_steps
                WHERE worker=? AND started_at >= ?
                """,
                (worker, cutoff)
            )
            for node, status, duration_ms, details_json in cur:
                nodes_executed += 1
                if isinstance(duration_ms, int):
                    sum_duration += duration_ms
                    count_duration += 1
                # Parse details lightly
                dj = None
                if details_json:
                    try:
                        dj = json.loads(details_json)
                    except Exception:
                        dj = None
                # Errors by category
                if status == 'failed' and isinstance(dj, dict):
                    err = dj.get('error') or {}
                    cat = err.get('category')
                    if cat in errors:
                        errors[cat] += 1
                # Retries: count _retry_ rows and attempts fields
                if '_retry_' in node:
                    retries_attempts += 1
                    parent = node.split('_retry_')[0]
                    nodes_with_retries.add(parent)
                elif isinstance(dj, dict) and isinstance(dj.get('attempts'), int) and dj['attempts'] > 1:
                    # attempts counts total tries; extra retries = attempts-1
                    retries_attempts += max(0, dj['attempts'] - 1)
                    nodes_with_retries.add(node)
                # LLM tokens (if usage available)
                if isinstance(dj, dict) and isinstance(dj.get('usage'), dict):
                    u = dj['usage']
                    try:
                        llm_tokens += int(u.get('prompt_tokens', 0)) + int(u.get('completion_tokens', 0))
                    except Exception:
                        pass
        finally:
            conn.close()
    except Exception:
        # On error, return minimal metrics instead of failing status
        return {
            "window": "0m",
            "nodes_executed": 0,
            "avg_duration_ms": 0,
            "errors": {"io": 0, "validation": 0, "permission": 0, "timeout": 0},
            "retries": {"attempts": 0, "nodes_with_retries": 0},
            "llm_tokens": 0
        }

    avg_duration = int(sum_duration / count_duration) if count_duration > 0 else 0
    # Compact window label
    label = f"{minutes//60}h" if minutes % 60 == 0 else f"{minutes}m"
    return {
        "window": label,
        "nodes_executed": nodes_executed,
        "avg_duration_ms": avg_duration,
        "errors": errors,
        "retries": {"attempts": retries_attempts, "nodes_with_retries": len(nodes_with_retries)},
        "llm_tokens": llm_tokens,
    }


def _parse_metrics_window_minutes(metrics_param: Dict[str, Any]) -> int:
    """Parse a compact window parameter (e.g., "5m", "15m", "1h") into minutes.
    Defaults to 60 if missing/invalid.
    """
    if not isinstance(metrics_param, dict):
        return 60
    win = metrics_param.get('window')
    if win is None:
        return 60
    try:
        if isinstance(win, (int, float)):
            return max(1, int(win))
        s = str(win).strip().lower()
        if s.endswith('m'):
            return max(1, int(s[:-1]))
        if s.endswith('h'):
            h = int(s[:-1])
            return max(1, h * 60)
        # raw number -> assume minutes
        return max(1, int(s))
    except Exception:
        return 60


def status(params: dict) -> dict:
    p = validate_params(params)
    worker_name = p['worker_name']
    db_path = db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": True, "status": "unknown", "worker_name": worker_name,
                "message": "No DB found (worker never started or DB deleted)", "truncated": False}

    phase = get_phase(db_path, worker_name) or 'unknown'
    pid_str = get_state_kv(db_path, worker_name, 'pid')
    hb = get_state_kv(db_path, worker_name, 'heartbeat')
    sleep_until = get_state_kv(db_path, worker_name, 'sleep_until')
    retry_next_at = get_state_kv(db_path, worker_name, 'retry_next_at')
    process_uid = get_state_kv(db_path, worker_name, 'process_uid')
    process_version = get_state_kv(db_path, worker_name, 'process_version')
    last_error = get_state_kv(db_path, worker_name, 'last_error')

    result = {"accepted": True, "status": phase, "worker_name": worker_name,
              "pid": int(pid_str) if pid_str and pid_str.isdigit() else None,
              "heartbeat": hb, "db_path": db_path, "truncated": False}
    if sleep_until: result['sleep_until'] = sleep_until
    if retry_next_at: result['retry_next_at'] = retry_next_at
    if process_uid: result['process_uid'] = process_uid
    if process_version: result['process_version'] = process_version
    if last_error: result['last_error'] = last_error[:400]

    # Optional compact metrics — only if explicitly requested
    include_metrics = False
    metrics_param = (params or {}).get('metrics') or {}
    include_metrics = bool(params.get('include_metrics')) or bool(metrics_param.get('include'))
    if include_metrics:
        minutes = _parse_metrics_window_minutes(metrics_param)
        result['metrics'] = _compute_metrics_window(db_path, worker_name, minutes)

    result.update(compact_errors_for_status(db_path, worker_name))
    result.update(debug_status_block(db_path, worker_name))
    return result


# === DEBUG CONTROL (synchronous step/continue/run_until) ===

def _write_json_kv(db_path: str, worker: str, key: str, value: Any):
    set_state_kv(db_path, worker, key, json.dumps(value))


def _wait_for_debug_pause(db_path: str, worker: str, req_id: str, timeout_sec: float = 10.0) -> Dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        phase = get_phase(db_path, worker)
        resp_id = get_state_kv(db_path, worker, 'debug.response_id') or ''
        if phase == 'debug_paused' and resp_id == req_id:
            last_step = get_state_kv(db_path, worker, 'debug.last_step')
            ctx_diff = get_state_kv(db_path, worker, 'debug.ctx_diff')
            next_node = get_state_kv(db_path, worker, 'debug.next_node') or ''
            cycle_id = get_state_kv(db_path, worker, 'debug.cycle_id') or ''
            step = json.loads(last_step) if last_step else {}
            diff = json.loads(ctx_diff) if ctx_diff else {"added":{},"changed":{},"deleted":[]}
            return { 'ready': True, 'step': step, 'ctx_cycle_diff': diff,
                     'next_node': next_node, 'cycle_id': cycle_id }
        time.sleep(0.15)
    return {'ready': False}


def debug_control(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'status'})  # ensure worker_name valid
    worker_name = p['worker_name']
    db_path = db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": False, "status": "error", "message": "Worker DB not found", "truncated": False}

    dbg = (params or {}).get('debug', {})
    action = dbg.get('action')
    if action not in {'enable','enable_now','step','continue','run_until','break_add','break_remove','break_clear','break_list','inspect','disable'}:
        return {"accepted": False, "status": "error", "message": f"Invalid debug action: {action}", "truncated": False}

    # Enable / enable_now
    if action in {'enable','enable_now'}:
        set_state_kv(db_path, worker_name, 'debug.enabled', 'true')
        set_state_kv(db_path, worker_name, 'debug.mode', 'step')
        pause_req = 'immediate' if action == 'enable_now' else 'next_boundary'
        set_state_kv(db_path, worker_name, 'debug.pause_request', pause_req)
        bps = dbg.get('breakpoints')
        if bps is not None:
            _write_json_kv(db_path, worker_name, 'debug.breakpoints', bps)
        return {"accepted": True, "status": "ok", "message": f"debug enabled ({pause_req})"}

    # Synchronous step/continue/run_until with timeout
    if action in {'step','continue','run_until'}:
        timeout_sec = float(dbg.get('timeout_sec', 10.0))
        if action == 'run_until':
            target = dbg.get('target') or {}
            _write_json_kv(db_path, worker_name, 'debug.until', target)
        req_id = str(uuid.uuid4())
        set_state_kv(db_path, worker_name, 'debug.req_id', req_id)
        set_state_kv(db_path, worker_name, 'debug.command', action)
        result = _wait_for_debug_pause(db_path, worker_name, req_id, timeout_sec)
        if result.get('ready'):
            out = {"accepted": True, "status": "ok", "in_progress": False}
            out.update({k: v for k, v in result.items() if k != 'ready'})
            return out
        # Not ready yet
        prev = get_state_kv(db_path, worker_name, 'debug.paused_at') or ''
        exec_node = get_state_kv(db_path, worker_name, 'debug.executing_node') or ''
        cycle_id = get_state_kv(db_path, worker_name, 'debug.cycle_id') or ''
        return {"accepted": True, "status": "in_progress", "message": "toujours en cours, demandez plus tard",
                "in_progress": True, "previous_node": prev, "executing_node": exec_node, "cycle_id": cycle_id,
                "timeout_sec": timeout_sec}

    # Breakpoints
    if action == 'break_clear':
        set_state_kv(db_path, worker_name, 'debug.command', 'break_clear')
        return {"accepted": True, "status": "ok", "message": "breakpoints cleared"}
    if action == 'break_add':
        cur = get_state_kv(db_path, worker_name, 'debug.breakpoints') or '[]'
        try:
            cur_list = json.loads(cur)
        except Exception:
            cur_list = []
        bp = {k: v for k, v in (dbg.get('breakpoint') or {}).items() if k in {'node','when'}}
        cur_list.append(bp)
        _write_json_kv(db_path, worker_name, 'debug.breakpoints', cur_list)
        return {"accepted": True, "status": "ok", "message": "breakpoint added"}
    if action == 'break_remove':
        cur = get_state_kv(db_path, worker_name, 'debug.breakpoints') or '[]'
        try:
            cur_list = json.loads(cur)
        except Exception:
            cur_list = []
        target = dbg.get('breakpoint') or {}
        cur_list = [b for b in cur_list if not (b.get('node')==target.get('node') and b.get('when')==target.get('when'))]
        _write_json_kv(db_path, worker_name, 'debug.breakpoints', cur_list)
        return {"accepted": True, "status": "ok", "message": "breakpoint removed"}

    if action == 'break_list':
        cur = get_state_kv(db_path, worker_name, 'debug.breakpoints') or '[]'
        return {"accepted": True, "status": "ok", "breakpoints": json.loads(cur)}

    if action == 'inspect':
        last_step = get_state_kv(db_path, worker_name, 'debug.last_step')
        ctx_diff = get_state_kv(db_path, worker_name, 'debug.ctx_diff')
        watches_values = get_state_kv(db_path, worker_name, 'debug.watches_values')
        out = {"accepted": True, "status": "ok", "step": json.loads(last_step) if last_step else {},
               "ctx_cycle_diff": json.loads(ctx_diff) if ctx_diff else {"added":{},"changed":{},"deleted":[]}}
        if watches_values:
            out['watches'] = json.loads(watches_values)
        return out

    if action == 'disable':
        set_state_kv(db_path, worker_name, 'debug.enabled', 'false')
        set_state_kv(db_path, worker_name, 'debug.command', 'disable')
        return {"accepted": True, "status": "ok", "message": "debug disabled"}

    return {"accepted": False, "status": "error", "message": "Unhandled debug action"}
