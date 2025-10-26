





from .validators import validate_params
from .._orchestrator.api_debug import debug_control as json_debug_control
from .api_spawn import db_path_for_worker
from .db import get_state_kv
import time

def _clamp_timeout(val: float) -> float:
    try:
        t = float(val)
    except Exception:
        t = 60.0  # default now 60s
    # allow long waits up to 300s for LLM/worker calls; min 0.1s
    if t <= 0:
        t = 60.0
    return max(0.1, min(t, 300.0))


def debug_control(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'debug'})

    # Fast-path checks (avoid useless waits)
    dbg_req = (params or {}).get('debug') or {}
    action = str(dbg_req.get('action') or '').lower()
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
