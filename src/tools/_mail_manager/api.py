import time, uuid, sys, subprocess, os, json
from .validators import validate_params
from .graph import build_execution_graph
from .db import get_db_path, set_state_kv, get_state_kv, utcnow_str, set_meta


def _make_job_id() -> str:
    return f"mailmgr_{int(time.time())}_{uuid.uuid4().hex[:6]}"

# ... helpers idem ...


def start_or_control(params: dict) -> dict:
    p = validate_params(params or {})
    op = p.get('operation', 'start')

    worker_name = p.get('worker_name')
    db_path = get_db_path(worker_name)

    if op == 'start':
        phase = get_state_kv(db_path, '__global__', 'phase')
        heartbeat = get_state_kv(db_path, '__global__', 'heartbeat')
        ttl_sec = int(p.get('poll_interval_minutes', 10)) * 60 * 3
        if phase in {'running','sleeping'} and heartbeat:
            import datetime as dt
            try:
                t = dt.datetime.strptime(heartbeat, '%Y-%m-%d %H:%M:%S')
                if (dt.datetime.utcnow() - t).total_seconds() < ttl_sec:
                    pid = get_state_kv(db_path, '__global__', 'pid')
                    return {"accepted": False, "status": "conflict", "message": "already running", "db_path": db_path, "phase": phase, "heartbeat": heartbeat, "pid": pid, "truncated": False}
            except Exception:
                pass
        saved_params = {
            'worker_name': worker_name,
            'persona': p.get('persona', ''),
            'mailboxes': p.get('mailboxes', []),
            'folders': p.get('folders', []),
            'poll_interval_minutes': p.get('poll_interval_minutes', 10),
            'mark_read': p.get('mark_read', True),
            'llm_model': p.get('llm_model', 'gpt-5-mini')
        }
        set_state_kv(db_path, '__global__', 'params', json.dumps(saved_params))
        set_state_kv(db_path, '__global__', 'phase', 'starting')
        set_state_kv(db_path, '__global__', 'heartbeat', utcnow_str())
        set_meta(db_path, 'worker_name', worker_name)
        set_meta(db_path, 'persona', p.get('persona', ''))
        graph = build_execution_graph(); set_state_kv(db_path, '__global__', 'graph_mermaid', graph['mermaid'])

        try:
            pid = _spawn_detached(db_path)
            set_state_kv(db_path, '__global__', 'pid', str(pid))
        except Exception as e:
            set_state_kv(db_path, '__global__', 'phase', 'failed'); set_state_kv(db_path, '__global__', 'last_error', f"spawn_failed: {e}")
            return {"accepted": False, "status": "failed", "message": f"spawn failed: {e}", "db_path": db_path, "truncated": False}

        return {"accepted": True, "status": "starting", "job_id": _make_job_id(), "db_path": db_path, "pid": pid, "graph_mermaid": graph["mermaid"], "heartbeat": get_state_kv(db_path, '__global__', 'heartbeat'), "truncated": False}

    if op == 'stop':
        set_state_kv(db_path, '__global__', 'cancel', 'true')
        # kill optionel idem ...
        return {"accepted": True, "status": "ok", "message": "cancel requested", "db_path": db_path, "truncated": False}

    if op == 'status':
        phase = get_state_kv(db_path, '__global__', 'phase') or 'unknown'
        pid = get_state_kv(db_path, '__global__', 'pid')
        heartbeat = get_state_kv(db_path, '__global__', 'heartbeat')
        sleep_until = get_state_kv(db_path, '__global__', 'sleep_until')
        worker = get_meta(db_path, 'worker_name')
        persona = get_meta(db_path, 'persona')
        return {"accepted": True, "status": phase, "pid": pid, "worker_name": worker, "persona": persona, "heartbeat": heartbeat, "sleep_until": sleep_until, "db_path": db_path, "truncated": False}

    return {"accepted": False, "status": "error", "message": "invalid operation"}
