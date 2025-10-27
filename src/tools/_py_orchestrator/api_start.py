from typing import Dict, Any
import uuid
from pathlib import Path
from .validators import validate_params
from .api_common import PROJECT_ROOT
from .db import init_db, get_state_kv, set_state_kv, get_phase, set_phase, heartbeat
from .api_spawn import spawn_runner, db_path_for_worker  # use py runner spawn
from src.tools._orchestrator.process_loader_core import ProcessLoadError  # reuse error type for symmetry
from src.tools._orchestrator.utils.time import utcnow_str


def _relpath_from_root(abs_path: str) -> str:
    try:
        p = Path(abs_path).resolve()
        root = PROJECT_ROOT.resolve()
        return p.relative_to(root).as_posix()
    except Exception:
        return abs_path


def start(params: dict) -> Dict[str, Any]:
    p = validate_params(params)
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
        'debug.step_trace', 'debug.trace'
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
