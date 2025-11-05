from __future__ import annotations
from typing import Dict, Any
import time
import json as _json

from .validators import validate_params
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv
from .api_debug_helpers import (
    long_timeout_or_default, db_max_rowid, db_rows_since, db_recent_window,
    read_step_snapshot,
)
from .api_debug_core import debug_movement_ack


def debug_stream(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'debug'})
    wn = p['worker_name']
    db_path = db_path_for_worker(wn)

    # Enable debug step mode immediately (KV-only)
    try:
        set_state_kv(db_path, wn, 'debug.enabled', 'true')
        set_state_kv(db_path, wn, 'debug.mode', 'step')
        set_state_kv(db_path, wn, 'debug.pause_request', 'immediate')
    except Exception:
        pass

    dbg_req = (params or {}).get('debug') or {}
    timeout_sec = long_timeout_or_default(dbg_req.get('timeout_sec'))
    deadline = (time.time() + timeout_sec) if (timeout_sec is not None) else None

    events = []
    tick = 0.2
    max_events = int(dbg_req.get('max_events') or 0)

    run_id = get_state_kv(db_path, wn, 'run_id') or ''
    
    # ✅ FIX: Vérifier run_id avant de démarrer
    if not run_id:
        return {
            'accepted': False,
            'status': 'error',
            'message': 'Worker has no active run_id (not started or crashed)',
            'events': [],
            'count': 0
        }
    
    last_rowid = db_max_rowid(db_path, wn, run_id)
    seen_sig = {}

    while True:
        if deadline is not None and time.time() > deadline:
            return {'accepted': True, 'status': 'timeout', 'events': events, 'count': len(events)}
        
        phase = get_state_kv(db_path, wn, 'phase') or ''
        if phase in {'completed','failed','canceled'}:
            call, lrp, ph, hb, last_err = read_step_snapshot(db_path, wn)
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

        # ✅ FIX: Détecter changement de run_id (worker restart)
        current_run_id = get_state_kv(db_path, wn, 'run_id') or ''
        if current_run_id != run_id:
            return {
                'accepted': True,
                'status': 'worker_restarted',
                'message': f'Worker restarted with new run_id. Old: {run_id[:8]}, New: {current_run_id[:8]}',
                'events': events,
                'count': len(events),
                'old_run_id': run_id,
                'new_run_id': current_run_id
            }

        rows = db_rows_since(db_path, wn, run_id, last_rowid)
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
                    return {'accepted': True, 'status': 'ok', 'events': events, 'count': len(events), 'truncated': True}
        else:
            time.sleep(tick)

        recent = db_recent_window(db_path, wn, run_id, window=10)
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
                    'chunk_type': ('error' if str(status).lower()== 'failed' else 'step'),
                    'node_executed': node,
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(db_path, wn, 'last_error') or '')} if str(status).lower()== 'failed' else None),
                    'phase': get_state_kv(db_path, wn, 'phase') or '',
                    'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                    'updated': True,
                })
                seen_sig[rid_i] = cur_sig
                if max_events and len(events) >= max_events:
                    return {'accepted': True, 'status': 'ok', 'events': events, 'count': len(events), 'truncated': True}
