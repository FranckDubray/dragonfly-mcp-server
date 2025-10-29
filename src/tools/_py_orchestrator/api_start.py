










from typing import Dict, Any
import uuid
from pathlib import Path
from .validators import validate_params
from .api_common import PROJECT_ROOT
from .db import init_db, get_state_kv, set_state_kv, get_phase, set_phase, heartbeat
from .api_spawn import spawn_runner, db_path_for_worker  # use py runner spawn
from .utils.time import utcnow_str


def _relpath_from_root(abs_path: str) -> str:
    try:
        p = Path(abs_path).resolve()
        root = PROJECT_ROOT.resolve()
        return p.relative_to(root).as_posix()
    except Exception:
        return abs_path


def _resolve_worker_file_safe(worker_name: str, worker_file: str | None) -> str | None:
    """Ergonomie: si worker_file est relatif ou absent, tenter workers/<name>/process.py.
    Retourne un chemin relatif 'workers/<name>/process.py' si trouvable, sinon None.
    """
    try:
        if worker_file and (worker_file.startswith('workers/') or worker_file.startswith('./workers/')):
            return worker_file
        # fallback auto
        candidate = Path(PROJECT_ROOT) / 'workers' / worker_name / 'process.py'
        if candidate.is_file():
            return candidate.relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        pass
    return None


def start(params: dict) -> Dict[str, Any]:
    # Valider sans écraser: on va améliorer l'ergonomie pour worker_file
    try:
        p = validate_params(params)
    except Exception:
        # Essayer fallback sur worker_file
        wn = str((params or {}).get('worker_name') or '').strip()
        wf = (params or {}).get('worker_file')
        auto = _resolve_worker_file_safe(wn, wf) if wn else None
        if not wn or not auto:
            # message clair au lieu de 500
            return {"accepted": False, "status": "error", "code": "WORKER_FILE_INVALID", "message": "worker_file doit être sous workers/<name>/process.py", "suggestions": ([f"workers/{wn}/process.py"] if wn else [])}
        # Rejouer avec le chemin auto
        p = validate_params({**params, 'worker_file': auto})

    worker_name = p['worker_name']
    worker_file = p['worker_file']
    worker_file_resolved = p['worker_file_resolved']
    hot_reload = p.get('hot_reload', True)

    db_path = db_path_for_worker(worker_name)
    init_db(db_path)

    set_phase(db_path, worker_name, 'starting')
    # Clear previous transient debug/py KV (extended purge)
    for key in [
        'cancel', 'last_error', 'py.last_summary', 'py.last_call', 'py.last_result_preview',
        'debug.enabled', 'debug.mode', 'debug.pause_request', 'debug.until', 'debug.breakpoints', 'debug.command',
        'debug.paused_at', 'debug.next_node', 'debug.cycle_id', 'debug.last_step', 'debug.ctx_diff',
        'debug.watches', 'debug.watches_values', 'debug.response_id', 'debug.req_id', 'debug.executing_node',
        'debug.previous_node',
        # new: also purge traces from a prior run
        'debug.step_trace', 'debug.trace',
        # also purge preflight artifacts from previous runs to avoid stale noise
        'py.graph_warnings', 'py.graph_errors'
    ]:
        try:
            set_state_kv(db_path, worker_name, key, '')
        except Exception:
            pass

    # Reset per-run LLM usage counters (avoid inheritance across runs)
    try:
        set_state_kv(db_path, worker_name, 'usage.llm.total_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.input_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.output_tokens', '0')
        set_state_kv(db_path, worker_name, 'usage.llm.by_model', '{}')
    except Exception:
        pass

    set_state_kv(db_path, worker_name, 'cancel', 'false')
    set_state_kv(db_path, worker_name, 'worker_name', worker_name)
    set_state_kv(db_path, worker_name, 'worker_file', worker_file)
    set_state_kv(db_path, worker_name, 'hot_reload', str(hot_reload).lower())

    # Also set __global__ context to the current worker (source of truth for runner bootstrap)
    try:
        set_state_kv(db_path, '__global__', 'worker_name', worker_name)
        set_state_kv(db_path, '__global__', 'worker_file', worker_file)
    except Exception:
        pass

    # Record the start of a new run (for filtering status/metrics)
    try:
        set_state_kv(db_path, worker_name, 'run_started_at', utcnow_str())
        set_state_kv(db_path, worker_name, 'run_id', str(uuid.uuid4()))
    except Exception:
        pass

    # Preflight à sec avant spawn (messages clairs)
    try:
        from .validation_core import validate_full
        pre = validate_full(worker_name, include_preflight=True, persist=False)
        if not pre.get('accepted'):
            # persister un résumé en KV pour l'UI
            try:
                import json as _json
                set_state_kv(db_path, worker_name, 'py.graph_errors', _json.dumps([it.get('message') for it in (pre.get('issues') or []) if (it.get('level')=='error')]) )
            except Exception:
                pass
            return {"accepted": False, "status": "error", "code": "PREFLIGHT_FAILED", "message": "Preflight failed (see issues)", "issues": pre.get('issues') or [], "preflight": pre.get('preflight') or {}}
    except Exception as e:
        # ne bloque pas le spawn si preflight à sec échoue anormalement; juste surface
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
        # Return db_path relative to project root for clean UI
        "db_path": _relpath_from_root(db_path),
        "heartbeat": get_state_kv(db_path, worker_name, 'heartbeat'),
        "truncated": False,
        "debug": {"enabled": debug_enabled_out, "pause_request": debug_pause_req_out}
    }
    return result
