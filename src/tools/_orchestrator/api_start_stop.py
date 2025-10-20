# Start/Stop operations (module <7KB)

import json
import importlib
from pathlib import Path
from typing import Any, Dict, Optional

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
# Ensure latest process_loader is used (dev hotpatch)
from . import process_loader as _process_loader
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
            "accepted": False, "status": "conflict", "worker_name": worker_name,
            "message": f"Worker already {phase} (recent heartbeat)", "db_path": db_path, "truncated": False
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
    heartbeat(db_path, worker_name)

    try:
        pid = spawn_runner(db_path, worker_name)
        set_state_kv(db_path, worker_name, 'pid', str(pid))
    except Exception as e:
        set_phase(db_path, worker_name, 'failed')
        set_state_kv(db_path, worker_name, 'last_error', str(e)[:400])
        return {"accepted": False, "status": "failed", "message": f"Failed to spawn runner: {str(e)[:200]}", "truncated": False}

    result = {
        "accepted": True, "status": "starting", "worker_name": worker_name, "pid": pid,
        "db_path": db_path, "heartbeat": get_state_kv(db_path, worker_name, 'heartbeat'),
        "process_uid": process_uid, "truncated": False
    }
    if process_version: result['process_version'] = process_version
    if graph_mermaid: result['graph_mermaid'] = graph_mermaid
    return result


def stop(params: dict) -> dict:
    import os, signal, subprocess

    p = validate_params(params)
    worker_name = p['worker_name']
    mode = p.get('stop', {}).get('mode', 'soft')

    db_path = db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": False, "status": "error", "message": f"Worker '{worker_name}' not found (no DB)", "truncated": False}

    pid_str = get_state_kv(db_path, worker_name, 'pid')
    pid = int(pid_str) if pid_str and pid_str.isdigit() else None

    if mode == 'soft':
        set_state_kv(db_path, worker_name, 'cancel', 'true')
        set_phase(db_path, worker_name, 'canceling')
        return {"accepted": True, "status": "ok", "message": "Cancel flag set (cooperative shutdown)", "pid": pid, "db_path": db_path, "truncated": False}

    if not pid:
        return {"accepted": False, "status": "error", "message": "No PID found (cannot send signal)", "db_path": db_path, "truncated": False}

    try:
        if mode == 'term':
            if os.name == 'nt': os.kill(pid, signal.CTRL_BREAK_EVENT)
            else: os.kill(pid, signal.SIGTERM)
            set_state_kv(db_path, worker_name, 'last_signal', 'SIGTERM')
            set_phase(db_path, worker_name, 'canceling')
            message = "SIGTERM sent"
        elif mode == 'kill':
            if os.name == 'nt': subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=False)
            else: os.kill(pid, signal.SIGKILL)
            set_state_kv(db_path, worker_name, 'last_signal', 'SIGKILL')
            set_phase(db_path, worker_name, 'failed')
            message = "SIGKILL sent (force kill)"
        else:
            return {"accepted": False, "status": "error", "message": f"Unknown mode: {mode}", "truncated": False}
        return {"accepted": True, "status": "ok", "message": message, "pid": pid, "db_path": db_path, "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Failed to send signal: {str(e)[:200]}", "pid": pid, "db_path": db_path, "truncated": False}
