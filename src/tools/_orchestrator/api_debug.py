
# Debug control helpers (<7KB)

import json
import time
import uuid
from typing import Any, Dict
from pathlib import Path

from .validators import validate_params
from .api_common import db_path_for_worker
from .db import get_state_kv, set_state_kv, get_phase
from .logging.crash_logger import get_recent_crashes


def _write_json_kv(db_path: str, worker: str, key: str, value: Any):
    set_state_kv(db_path, worker, key, json.dumps(value))


def _collect_failure_snapshot(db_path: str, worker: str) -> Dict[str, Any]:
    snap: Dict[str, Any] = {
        'phase': get_phase(db_path, worker) or 'unknown',
        'last_error': get_state_kv(db_path, worker, 'last_error') or '',
        'phase_trace': get_state_kv(db_path, worker, 'debug.phase_trace') or ''
    }
    try:
        crashes = get_recent_crashes(db_path, worker, limit=1)
        if crashes:
            snap['crash'] = crashes[0]
    except Exception:
        pass
    return snap


def _wait_for_debug_pause(db_path: str, worker: str, req_id: str, timeout_sec: float = 10.0) -> Dict[str, Any]:
    t0 = time.time()
    poll = 0.03  # tighter poll to catch very fast nodes
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
        # Detect terminal/failure phases early and surface info
        if phase in {'failed','completed','canceled'}:
            return {'ready': False, 'terminal': True, 'phase': phase, 'snapshot': _collect_failure_snapshot(db_path, worker)}
        time.sleep(poll)
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
        # Optional breakpoints set
        bps = dbg.get('breakpoints')
        if bps is not None:
            _write_json_kv(db_path, worker_name, 'debug.breakpoints', bps)
        # Normalize transient state to avoid stale handshake
        set_state_kv(db_path, worker_name, 'debug.command', 'none')
        set_state_kv(db_path, worker_name, 'debug.req_id', '')
        set_state_kv(db_path, worker_name, 'debug.response_id', '')
        for key in ['debug.paused_at','debug.last_step','debug.ctx_diff','debug.executing_node','debug.next_node','debug.previous_node']:
            try:
                set_state_kv(db_path, worker_name, key, '')
            except Exception:
                pass
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
        # Optional small trace for diagnosis
        try:
            set_state_kv(db_path, worker_name, 'debug.step_trace', f"issued:{action}:{req_id}")
        except Exception:
            pass
        result = _wait_for_debug_pause(db_path, worker_name, req_id, timeout_sec)
        if result.get('ready'):
            out = {"accepted": True, "status": "ok", "in_progress": False}
            out.update({k: v for k, v in result.items() if k != 'ready'})
            return out
        # Terminal or failure detected
        if result.get('terminal'):
            snap = result.get('snapshot') or {}
            return {
                "accepted": False,
                "status": result.get('phase') or 'failed',
                "error": {
                    "message": snap.get('last_error') or f"runner in terminal phase: {result.get('phase')}",
                    "phase": result.get('phase'),
                    "phase_trace": snap.get('phase_trace',''),
                    "crash": snap.get('crash')
                },
                "truncated": False
            }
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
