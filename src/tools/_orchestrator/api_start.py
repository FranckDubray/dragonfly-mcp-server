
# Start operation (split from api_start_stop, keep file <7KB)

import importlib
import uuid
from .validators import validate_params
from .api_common import (
    compute_process_uid,
    db_path_for_worker,
    check_heartbeat_fresh,
    spawn_runner,
    validate_process_schema,
    validate_process_logic,
)
from .db import init_db, get_state_kv, set_state_kv, get_phase, set_phase, heartbeat
from .utils import utcnow_str
from . import process_loader as _process_loader

# Ensure latest process_loader is used (dev hotpatch)
importlib.reload(_process_loader)
load_process_with_imports = _process_loader.load_process_with_imports
ProcessLoadError = _process_loader.ProcessLoadError


def start(params: dict) -> dict:
    p = validate_params(params)
    worker_name = p['worker_name']
    worker_file = p['worker_file']
    worker_file_resolved = p['worker_file_resolved']
    hot_reload = p.get('hot_reload', True)

    db_path = db_path_for_worker(worker_name)
    init_db(db_path)

    phase = get_phase(db_path, worker_name)
    if phase in {'running', 'sleeping'} and check_heartbeat_fresh(db_path, worker_name, ttl_seconds=90):
        return {
            "accepted": False,
            "status": "conflict",
            "worker_name": worker_name,
            "message": f"Worker already {phase} (recent heartbeat)",
            "db_path": db_path,
            "truncated": False,
        }

    try:
        process_data = load_process_with_imports(worker_file_resolved)
    except ProcessLoadError as e:
        return {"accepted": False, "status": "failed", "message": f"Failed to load process: {str(e)[:200]}", "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "failed", "message": f"Unexpected error loading process: {str(e)[:200]}", "truncated": False}

    schema_error = validate_process_schema(process_data)
    if schema_error:
        return schema_error

    logic_error = validate_process_logic(process_data)
    if logic_error:
        return {"accepted": False, "status": "failed", "message": f"Process validation failed: {logic_error}", "truncated": False}

    process_uid = compute_process_uid(worker_file_resolved)
    process_version = process_data.get('process_version')
    graph_mermaid = process_data.get('graph_mermaid')

    set_phase(db_path, worker_name, 'starting')
    set_state_kv(db_path, worker_name, 'cancel', 'false')
    set_state_kv(db_path, worker_name, 'worker_name', worker_name)
    set_state_kv(db_path, worker_name, 'worker_file', worker_file)
    set_state_kv(db_path, worker_name, 'process_uid', process_uid)
    if process_version:
        set_state_kv(db_path, worker_name, 'process_version', str(process_version))
    set_state_kv(db_path, worker_name, 'hot_reload', str(hot_reload).lower())

    # Record the start of a new run (for filtering status/metrics)
    try:
        set_state_kv(db_path, worker_name, 'run_started_at', utcnow_str())
        set_state_kv(db_path, worker_name, 'run_id', str(uuid.uuid4()))
    except Exception:
        pass

    # Start directly in debug if requested (supports legacy keys), otherwise reset stale debug state
    dbg = (params or {}).get('debug') or {}
    action = str(dbg.get('action') or '').lower()
    pause_at_start = bool(dbg.get('pause_at_start'))
    enable_on_start = bool(dbg.get('enable_on_start'))
    enabled_flag = dbg.get('enabled')  # optional boolean

    want_debug_start = bool(enable_on_start or pause_at_start or action in {'enable', 'enable_now'} or (enabled_flag is True))

    debug_enabled_out = False
    debug_pause_req_out = ''

    if want_debug_start:
        # Purge any stale transient debug state before enabling
        for key in [
            'debug.mode','debug.pause_request','debug.until','debug.breakpoints','debug.command',
            'debug.paused_at','debug.next_node','debug.cycle_id','debug.last_step','debug.ctx_diff',
            'debug.watches','debug.watches_values','debug.response_id','debug.req_id','debug.executing_node',
            'debug.previous_node','last_error'
        ]:
            try:
                set_state_kv(db_path, worker_name, key, '')
            except Exception:
                pass
        set_state_kv(db_path, worker_name, 'debug.enabled', 'true')
        set_state_kv(db_path, worker_name, 'debug.mode', 'step')
        # Determine pause behavior: immediate if explicit, else next_boundary
        pause_req = 'immediate' if (pause_at_start or enable_on_start or action == 'enable_now') else 'next_boundary'
        set_state_kv(db_path, worker_name, 'debug.pause_request', pause_req)
        debug_enabled_out = True
        debug_pause_req_out = pause_req
    else:
        # Reset stale debug flags from previous runs AND clear last_error
        set_state_kv(db_path, worker_name, 'debug.enabled', 'false')
        for key in [
            'debug.mode','debug.pause_request','debug.until','debug.breakpoints','debug.command',
            'debug.paused_at','debug.next_node','debug.cycle_id','debug.last_step','debug.ctx_diff',
            'debug.watches','debug.watches_values','debug.response_id','debug.req_id','debug.executing_node',
            'debug.previous_node','last_error'
        ]:
            set_state_kv(db_path, worker_name, key, '')

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
        "db_path": db_path,
        "heartbeat": get_state_kv(db_path, worker_name, 'heartbeat'),
        "process_uid": process_uid,
        "truncated": False,
    }
    if process_version:
        result['process_version'] = process_version
    if graph_mermaid:
        result['graph_mermaid'] = graph_mermaid
    # NEW: surface debug state in start response for observability
    result['debug'] = {"enabled": debug_enabled_out, "pause_request": debug_pause_req_out}
    return result
