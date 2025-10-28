
from __future__ import annotations
from typing import Dict, Any
import time

from .validators import validate_params
from .._orchestrator.api_debug import debug_control as json_debug_control
from .api_spawn import db_path_for_worker
from .db import get_state_kv
from .api_debug_helpers import clamp_timeout


def debug_movement_ack(params: dict, base_res: Dict[str, Any]) -> Dict[str, Any]:
    """Add robust ACK for step/continue/run_until. Returns enriched response."""
    p = validate_params({**params, 'operation': 'debug'})
    wn = p['worker_name']
    dbp = db_path_for_worker(wn)
    dbg_req = (params or {}).get('debug') or {}
    action = str(dbg_req.get('action') or '').lower()

    try:
        timeout = clamp_timeout(dbg_req.get('timeout_sec', 60.0))
        if action in {'step','continue','run_until'} and timeout > 0:
            deadline = time.time() + timeout
            tick = 0.2
            long_hint = (get_state_kv(dbp, wn, 'debug.executing_node') or '').endswith('STEP_SLEEP')
            if long_hint and timeout < 65:
                deadline = time.time() + 65
            last_seen_exec = get_state_kv(dbp, wn, 'debug.executing_node') or ''
            while time.time() < deadline:
                paused_at = get_state_kv(dbp, wn, 'debug.paused_at') or ''
                next_node = get_state_kv(dbp, wn, 'debug.next_node') or ''
                if paused_at or next_node:
                    cycle_id = get_state_kv(dbp, wn, 'debug.cycle_id') or ''
                    paused_out = paused_at or next_node
                    return {'accepted': True, 'status': 'paused', 'paused_at': paused_out, 'cycle_id': cycle_id}
                cur_exec = get_state_kv(dbp, wn, 'debug.executing_node') or ''
                if last_seen_exec and not cur_exec:
                    time.sleep(0.2)
                last_seen_exec = cur_exec
                phase = get_state_kv(dbp, wn, 'phase') or ''
                if phase in {'completed','failed','canceled'}:
                    return {'accepted': True, 'status': phase}
                time.sleep(tick)
    except Exception:
        pass
    return base_res
