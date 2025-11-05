"""Streaming observation mode - yields events one by one."""

from __future__ import annotations
from typing import Iterator, Dict, Any
import time
import json as _json

from .api_spawn import db_path_for_worker
from .db import get_state_kv
from .api_observe import (
    _long_timeout_or_default,
    _db_max_rowid,
    _db_rows_since,
    _db_recent_window,
)


def observe_stream(params: dict) -> Iterator[Dict[str, Any]]:
    """
    Generator that yields observation events one by one (streaming mode).
    
    Each event is a dict with:
    - chunk_type: 'step' | 'error' | 'terminal' | 'status'
    - node_executed, node_next, io, phase, heartbeat, cycle_id, duration_ms
    - updated: bool (if it's an update to existing step)
    - last_rowid: int (for resuming stream later)
    
    Yields events as they happen, enabling real-time UI updates.
    Supports resuming from a specific rowid via 'from_rowid' parameter.
    """
    wn = str((params or {}).get('worker_name') or '').strip()
    if not wn:
        yield {
            'chunk_type': 'error',
            'error': {'message': 'worker_name required'},
            'terminal': True
        }
        return

    db_path = db_path_for_worker(wn)
    obs_req = (params or {}).get('observe') or {}

    # Config
    window_size = int(obs_req.get('window_size') or 50)  # Augmenté de 10 à 50
    try:
        window_size = max(1, min(500, window_size))
    except Exception:
        window_size = 50
    
    tick = float(obs_req.get('tick_sec') or 0.2)
    try:
        tick = max(0.1, min(2.0, tick))
    except Exception:
        tick = 0.2

    timeout_sec = _long_timeout_or_default(obs_req.get('timeout_sec'))
    deadline = (time.time() + timeout_sec) if (timeout_sec is not None) else None

    max_events = int(obs_req.get('max_events') or 0)
    event_count = 0

    run_id = get_state_kv(db_path, wn, 'run_id') or ''
    
    # ✅ FIX: Si run_id est vide, ne pas utiliser from_rowid (évite pollution)
    if not run_id:
        yield {
            'chunk_type': 'error',
            'error': {'message': 'Worker has no active run_id (not started or crashed)'},
            'terminal': True,
            'worker_name': wn
        }
        return
    
    # 🆕 Support for resuming from specific rowid
    from_rowid = obs_req.get('from_rowid')
    if from_rowid is not None:
        try:
            last_rowid = int(from_rowid)
        except Exception:
            last_rowid = _db_max_rowid(db_path, wn, run_id)
    else:
        last_rowid = _db_max_rowid(db_path, wn, run_id)
    
    seen_sig = {}
    idle_loops = 0

    # Yield initial status event with resume info
    try:
        phase = get_state_kv(db_path, wn, 'phase') or 'unknown'
        heartbeat = get_state_kv(db_path, wn, 'heartbeat') or ''
        yield {
            'chunk_type': 'status',
            'phase': phase,
            'heartbeat': heartbeat,
            'worker_name': wn,
            'run_id': run_id,  # ✅ Expose run_id pour détection de restart
            'last_rowid': last_rowid,  # 🆕 Client peut sauvegarder pour resume
            'resume_from': from_rowid,  # 🆕 Echo du paramètre
        }
    except Exception:
        pass

    while True:
        # Timeout check
        if deadline is not None and time.time() > deadline:
            yield {
                'chunk_type': 'terminal',
                'reason': 'timeout',
                'event_count': event_count,
                'last_rowid': last_rowid,  # 🆕 Pour resume
            }
            return

        # Terminal phase check
        phase = get_state_kv(db_path, wn, 'phase') or ''
        if phase in {'completed', 'failed', 'canceled'}:
            call = ''
            lrp = ''
            try:
                call = get_state_kv(db_path, wn, 'py.last_call') or ''
                lrp = get_state_kv(db_path, wn, 'py.last_result_preview') or ''
            except Exception:
                pass
            
            yield {
                'chunk_type': ('error' if (phase == 'failed') else 'terminal'),
                'node_executed': '',
                'node_next': '',
                'io': {'in': call, 'out_preview': lrp},
                'error': ({'message': get_state_kv(db_path, wn, 'last_error') or ''} if phase == 'failed' else None),
                'phase': phase,
                'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                'cycle_id': get_state_kv(db_path, wn, 'debug.cycle_id') or '',
                'terminal': True,
                'event_count': event_count,
                'last_rowid': last_rowid,  # 🆕 Pour resume
            }
            return

        # ✅ FIX: Vérifier si run_id a changé (worker restart)
        current_run_id = get_state_kv(db_path, wn, 'run_id') or ''
        if current_run_id != run_id:
            yield {
                'chunk_type': 'terminal',
                'reason': 'worker_restarted',
                'event_count': event_count,
                'last_rowid': last_rowid,
                'old_run_id': run_id,
                'new_run_id': current_run_id,
                'message': 'Worker restarted with new run_id. Please restart observation with from_rowid=0.'
            }
            return

        # New inserts
        rows = _db_rows_since(db_path, wn, run_id, last_rowid)
        if rows:
            idle_loops = 0
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
                except Exception as e:
                    # 🆕 Log parsing errors instead of silent fail
                    lrp = f"[JSON parse error: {str(e)[:100]}]"
                
                event = {
                    'chunk_type': ('error' if str(status).lower() == 'failed' else 'step'),
                    'node_executed': node,
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(db_path, wn, 'last_error') or '')} if str(status).lower() == 'failed' else None),
                    'phase': get_state_kv(db_path, wn, 'phase') or '',
                    'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                    'last_rowid': int(rid),  # 🆕 Pour resume
                }
                
                yield event
                event_count += 1
                
                # Track signature
                sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
                seen_sig[int(rid)] = sig
                last_rowid = int(rid)
                
                # Max events limit
                if max_events and event_count >= max_events:
                    yield {
                        'chunk_type': 'terminal',
                        'reason': 'max_events_reached',
                        'event_count': event_count,
                        'last_rowid': last_rowid,  # 🆕 Pour resume
                    }
                    return
        else:
            # Backoff if idle
            idle_loops += 1
            sleep_for = tick if idle_loops < 5 else min(1.0, tick * 2)
            time.sleep(sleep_for)

        # Check updates in recent window
        recent = _db_recent_window(db_path, wn, run_id, window=window_size)
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
                except Exception as e:
                    # 🆕 Log parsing errors
                    lrp = f"[JSON parse error: {str(e)[:100]}]"
                
                event = {
                    'chunk_type': ('error' if str(status).lower() == 'failed' else 'step'),
                    'node_executed': node,
                    'node_next': '',
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(db_path, wn, 'last_error') or '')} if str(status).lower() == 'failed' else None),
                    'phase': get_state_kv(db_path, wn, 'phase') or '',
                    'heartbeat': get_state_kv(db_path, wn, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                    'updated': True,  # 🚨 Update flag
                    'last_rowid': int(rid),  # 🆕 Pour resume
                }
                
                yield event
                event_count += 1
                seen_sig[rid_i] = cur_sig
                
                if max_events and event_count >= max_events:
                    yield {
                        'chunk_type': 'terminal',
                        'reason': 'max_events_reached',
                        'event_count': event_count,
                        'last_rowid': last_rowid,  # 🆕 Pour resume
                    }
                    return
