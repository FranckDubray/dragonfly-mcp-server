
















from .validators import validate_params
from .._orchestrator.api_debug import debug_control as json_debug_control
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv

# New split modules
from .api_debug_stream import debug_stream as _debug_stream
from .api_debug_inspect import debug_inspect as _debug_inspect
from .api_debug_core import debug_movement_ack as _debug_movement_ack


def debug_control(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'debug'})

    dbg_req = (params or {}).get('debug') or {}
    action = str(dbg_req.get('action') or '').lower()
    if action == 'stream':
        return _debug_stream(params)

    # Terminal phases: do not attempt debug changes
    db_path = db_path_for_worker(p['worker_name'])
    try:
        phase = get_state_kv(db_path, p['worker_name'], 'phase') or ''
        if phase in {'completed', 'failed', 'canceled'}:
            return {'accepted': False, 'status': 'terminal', 'message': f'Worker is in terminal phase: {phase}'}
    except Exception:
        pass

    # Fast-path enable
    if action in {'enable', 'enable_now'}:
        try:
            dbg_enabled = (get_state_kv(db_path, p['worker_name'], 'debug.enabled') == 'true')
            if dbg_enabled:
                return {'accepted': True, 'status': 'already_enabled'}
        except Exception:
            pass

    # Delegate to JSON orchestrator
    res = json_debug_control({'operation':'debug','worker_name': p['worker_name'], 'debug': dbg_req})

    # Enrich inspect
    if action == 'inspect' and isinstance(res, dict) and res.get('accepted'):
        res = _debug_inspect(params, res)

    # Robust ACK for movement actions
    if action in {'step','continue','run_until'}:
        res = _debug_movement_ack(params, res)

    return res
