from typing import Dict, Any
import uuid
from pathlib import Path

from .validators import validate_params
from .api_common import PROJECT_ROOT
from .db import init_db, get_state_kv, set_state_kv, set_phase, heartbeat
from .api_spawn import spawn_runner, db_path_for_worker
from .utils.time import utcnow_str

# New split helpers
from .start_helpers import relpath_from_root, resolve_worker_file_safe, slugify, derive_from_template
from .start_identity import ensure_identity, ensure_leader_db
from .start_prelude import reset_transients, reset_llm_usage


def start(params: dict) -> Dict[str, Any]:
    # Ergonomie: si new_worker:{first_name, template} est fourni, dériver automatiquement worker_name et worker_file
    auto = derive_from_template(params)
    if auto and (not params.get('worker_name') or not params.get('worker_file')):
        params = {**params, **auto}

    # Valider sans écraser: on va améliorer l'ergonomie pour worker_file
    try:
        p = validate_params(params)
    except Exception:
        # Essayer fallback sur worker_file
        wn = str((params or {}).get('worker_name') or '').strip()
        wf = (params or {}).get('worker_file')
        auto2 = resolve_worker_file_safe(wn, wf) if wn else None
        if not wn or not auto2:
            return {"accepted": False, "status": "error", "code": "WORKER_FILE_INVALID", "message": "worker_file doit être sous workers/<name>/process.py", "suggestions": ([f"workers/{wn}/process.py"] if wn else [])}
        p = validate_params({**params, 'worker_file': auto2})

    worker_name = p['worker_name']
    worker_file = p['worker_file']
    hot_reload = p.get('hot_reload', True)

    # Leader optionnel
    leader = None
    try:
        leader_obj = (params or {}).get('leader') or {}
        leader_name = str(leader_obj.get('name') or '').strip()
        if leader_name:
            ensure_leader_db(leader_name)
            leader = slugify(leader_name)
    except Exception:
        pass

    db_path = db_path_for_worker(worker_name)
    init_db(db_path)

    # Inject instance DB name into metadata (will be merged by runner)
    try:
        instance_db_file = f"worker_{worker_name}.db"
        import json as _json
        md = {}
        try:
            md = _json.loads(get_state_kv(db_path, worker_name, 'py.process_metadata') or '{}')
        except:
            pass
        md['db_file'] = instance_db_file
        set_state_kv(db_path, worker_name, 'py.process_metadata', _json.dumps(md))
    except Exception:
        pass

    # Créer/mettre à jour l'identité si new_worker fourni (inclure leader si présent)
    try:
        nw = (params or {}).get('new_worker') or {}
        first = str(nw.get('first_name') or '').strip()
        template = str(nw.get('template') or '').strip()
        if first and template:
            ensure_identity(db_path, worker_name, template, first, leader)
    except Exception:
        pass

    set_phase(db_path, worker_name, 'starting')

    # Reset transients + LLM usage counters
    reset_transients(db_path, worker_name)
    reset_llm_usage(db_path, worker_name)

    # Persist basic KV
    set_state_kv(db_path, worker_name, 'cancel', 'false')
    set_state_kv(db_path, worker_name, 'worker_name', worker_name)
    set_state_kv(db_path, worker_name, 'worker_file', worker_file)
    set_state_kv(db_path, worker_name, 'hot_reload', str(hot_reload).lower())

    # Also set __global__ context
    try:
        set_state_kv(db_path, '__global__', 'worker_name', worker_name)
        set_state_kv(db_path, '__global__', 'worker_file', worker_file)
    except Exception:
        pass

    # Record new run
    try:
        set_state_kv(db_path, worker_name, 'run_started_at', utcnow_str())
        set_state_kv(db_path, worker_name, 'run_id', str(uuid.uuid4()))
    except Exception:
        pass

    # Preflight (tolérance root manquant si worker_file OK)
    try:
        from .validation_core import validate_full
        pre = validate_full(worker_name, include_preflight=True, persist=False)
        if not pre.get('accepted'):
            try:
                issues = pre.get('issues') or []
                messages = [str(it.get('message') or '') for it in issues]
                root_err = any('Worker root not found' in m for m in messages)
                wf_ok = Path(PROJECT_ROOT / worker_file).is_file() or Path(worker_file).is_file()
                if root_err and wf_ok:
                    import json as _json
                    set_state_kv(db_path, worker_name, 'py.graph_warnings', _json.dumps(messages, ensure_ascii=False))
                else:
                    try:
                        import json as _json
                        set_state_kv(db_path, worker_name, 'py.graph_errors', _json.dumps([it.get('message') for it in issues if (it.get('level')=='error')]))
                    except Exception:
                        pass
                    return {"accepted": False, "status": "error", "code": "PREFLIGHT_FAILED", "message": "Preflight failed (see issues)", "issues": pre.get('issues') or [], "preflight": pre.get('preflight') or {}}
            except Exception:
                return {"accepted": False, "status": "error", "code": "PREFLIGHT_FAILED", "message": "Preflight failed (unexpected)", "issues": pre.get('issues') or []}
    except Exception as e:
        try:
            set_state_kv(db_path, worker_name, 'last_error', f"Preflight(dry) exception: {str(e)[:200]}")
        except Exception:
            pass

    # Debug arming
    dbg = (params or {}).get('debug') or {}
    action = str(dbg.get('action') or '').lower()
    pause_at_start = bool(dbg.get('pause_at_start'))
    enable_on_start = bool(dbg.get('enable_on_start'))
    enabled_flag = dbg.get('enabled')
    want_debug_start = bool(enable_on_start or pause_at_start or action in {'enable','enable_now'} or (enabled_flag is True))

    debug_enabled_out = False
    debug_pause_req_out = ''
    if want_debug_start:
        set_state_kv(db_path, worker_name, 'debug.enabled', 'true')
        set_state_kv(db_path, worker_name, 'debug.mode', 'step')
        pause_req = 'immediate' if (pause_at_start or enable_on_start or action == 'enable_now') else 'next_boundary'
        set_state_kv(db_path, worker_name, 'debug.pause_request', pause_req)
        debug_enabled_out = True
        debug_pause_req_out = pause_req
    else:
        set_state_kv(db_path, worker_name, 'debug.enabled', 'false')

    heartbeat(db_path, worker_name)

    try:
        pid = spawn_runner(db_path, worker_name)
        set_state_kv(db_path, worker_name, 'pid', str(pid))
    except Exception as e:
        set_phase(db_path, worker_name, 'failed')
        set_state_kv(db_path, worker_name, 'last_error', str(e)[:400])
        return {"accepted": False, "status": "failed", "message": f"Failed to spawn runner: {str(e)[:200]}", "truncated": False}

    result = {
        "accepted": True,
        "status": "starting",
        "worker_name": worker_name,
        "pid": pid,
        "db_path": relpath_from_root(db_path),
        "heartbeat": get_state_kv(db_path, worker_name, 'heartbeat'),
        "truncated": False,
        "debug": {"enabled": debug_enabled_out, "pause_request": debug_pause_req_out}
    }
    return result
