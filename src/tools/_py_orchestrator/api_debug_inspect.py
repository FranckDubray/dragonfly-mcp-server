
from __future__ import annotations
from typing import Dict, Any

from .validators import validate_params
from .api_spawn import db_path_for_worker
from .db import get_state_kv


def debug_inspect(params: dict, base_res: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich inspect result to never be empty. Merge with base_res."""
    p = validate_params({**params, 'operation': 'debug'})
    wn = p['worker_name']
    dbp = db_path_for_worker(wn)

    try:
        call = get_state_kv(dbp, wn, 'py.last_call') or ''
        lrp  = get_state_kv(dbp, wn, 'py.last_result_preview') or ''
        execn = get_state_kv(dbp, wn, 'debug.executing_node') or ''
        prevn = get_state_kv(dbp, wn, 'debug.previous_node') or ''
        nextn = get_state_kv(dbp, wn, 'debug.next_node') or ''
        paused_at = get_state_kv(dbp, wn, 'debug.paused_at') or ''
        base_res = dict(base_res or {})
        base_res.setdefault('nodes', {})
        base_res['nodes'].update({'previous_node': prevn, 'executing_node': execn, 'paused_at': paused_at, 'next_node': nextn})
        base_res['io'] = {'in': call, 'out_preview': lrp}
        if not base_res.get('step'):
            node_hint = paused_at or execn or prevn
            if node_hint:
                base_res['step'] = {'node': node_hint, 'type': 'py_step'}
        return base_res
    except Exception:
        return base_res
