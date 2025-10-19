# Orchestrator tool API (start/stop/status controller)
# No business logic here; strict validation + state persistence + runner spawn.

import json
import hashlib
import subprocess
import sys
import signal
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from .validators import validate_params
from .db import init_db, get_state_kv, set_state_kv, get_phase, set_phase, heartbeat
from .process_loader import load_process_with_imports, ProcessLoadError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SQLITE_DIR = PROJECT_ROOT / 'sqlite3'
LOG_DIR = PROJECT_ROOT / 'logs'


def _compute_process_uid(worker_file_resolved: str) -> str:
    """SHA256 hash of worker_file content (short 12 chars)"""
    with open(worker_file_resolved, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _db_path_for_worker(worker_name: str) -> str:
    """Compute DB path: sqlite3/worker_<safe>.db"""
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    return str(SQLITE_DIR / f"worker_{worker_name}.db")


def _check_heartbeat_fresh(db_path: str, worker: str, ttl_seconds: int = 90) -> bool:
    """Check if heartbeat is recent (within TTL)"""
    hb = get_state_kv(db_path, worker, 'heartbeat')
    if not hb:
        return False
    try:
        hb_dt = datetime.fromisoformat(hb.replace(' ', 'T'))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (now - hb_dt).total_seconds() < ttl_seconds
    except:
        return False


def _spawn_runner(db_path: str, worker_name: str) -> int:
    """Spawn detached runner process (OS-aware), return PID. Stdout/err -> logs/worker_<name>.log"""
    cmd = [sys.executable, '-m', 'src.tools._orchestrator.runner', db_path]

    # Ensure logs dir
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"worker_{worker_name}.log"
    log_fh = open(log_path, 'ab', buffering=0)

    if os.name == 'nt':
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            creationflags=flags,
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=log_fh,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=log_fh,
            stderr=log_fh,
        )

    return proc.pid


def start(params: dict) -> dict:
    """Start operation: validate, persist, spawn runner"""
    p = validate_params(params)
    worker_name = p['worker_name']
    worker_file = p['worker_file']
    worker_file_resolved = p['worker_file_resolved']
    hot_reload = p.get('hot_reload', True)

    db_path = _db_path_for_worker(worker_name)
    init_db(db_path)

    # Conflict check
    phase = get_phase(db_path, worker_name)
    if phase in {'running', 'sleeping'} and _check_heartbeat_fresh(db_path, worker_name, ttl_seconds=90):
        return {
            "accepted": False,
            "status": "conflict",
            "worker_name": worker_name,
            "message": f"Worker already {phase} (recent heartbeat)",
            "db_path": db_path,
            "truncated": False
        }

    # Load worker_file with $import support
    try:
        process_data = load_process_with_imports(worker_file_resolved)
    except ProcessLoadError as e:
        return {
            "accepted": False,
            "status": "failed",
            "message": f"Failed to load process: {str(e)[:200]}",
            "truncated": False
        }
    except Exception as e:
        return {
            "accepted": False,
            "status": "failed",
            "message": f"Unexpected error loading process: {str(e)[:200]}",
            "truncated": False
        }

    process_uid = _compute_process_uid(worker_file_resolved)
    process_version = process_data.get('process_version')
    graph_mermaid = process_data.get('graph_mermaid')

    # Persist state
    set_phase(db_path, worker_name, 'starting')
    set_state_kv(db_path, worker_name, 'cancel', 'false')
    set_state_kv(db_path, worker_name, 'worker_name', worker_name)
    set_state_kv(db_path, worker_name, 'worker_file', worker_file)
    set_state_kv(db_path, worker_name, 'process_uid', process_uid)
    if process_version:
        set_state_kv(db_path, worker_name, 'process_version', str(process_version))
    set_state_kv(db_path, worker_name, 'hot_reload', str(hot_reload).lower())
    heartbeat(db_path, worker_name)

    # Spawn runner with log redirection
    try:
        pid = _spawn_runner(db_path, worker_name)
        set_state_kv(db_path, worker_name, 'pid', str(pid))
    except Exception as e:
        set_phase(db_path, worker_name, 'failed')
        set_state_kv(db_path, worker_name, 'last_error', str(e)[:400])
        return {
            "accepted": False,
            "status": "failed",
            "message": f"Failed to spawn runner: {str(e)[:200]}",
            "truncated": False
        }

    result = {
        "accepted": True,
        "status": "starting",
        "worker_name": worker_name,
        "pid": pid,
        "db_path": db_path,
        "heartbeat": get_state_kv(db_path, worker_name, 'heartbeat'),
        "process_uid": process_uid,
        "truncated": False
    }

    if process_version:
        result['process_version'] = process_version
    if graph_mermaid:
        result['graph_mermaid'] = graph_mermaid

    return result


def stop(params: dict) -> dict:
    p = validate_params(params)
    worker_name = p['worker_name']
    mode = p.get('stop', {}).get('mode', 'soft')

    db_path = _db_path_for_worker(worker_name)
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


def status(params: dict) -> dict:
    p = validate_params(params)
    worker_name = p['worker_name']

    db_path = _db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": True, "status": "unknown", "worker_name": worker_name, "message": "No DB found (worker never started or DB deleted)", "truncated": False}

    phase = get_phase(db_path, worker_name) or 'unknown'
    pid_str = get_state_kv(db_path, worker_name, 'pid')
    hb = get_state_kv(db_path, worker_name, 'heartbeat')
    sleep_until = get_state_kv(db_path, worker_name, 'sleep_until')
    retry_next_at = get_state_kv(db_path, worker_name, 'retry_next_at')
    process_uid = get_state_kv(db_path, worker_name, 'process_uid')
    process_version = get_state_kv(db_path, worker_name, 'process_version')
    last_error = get_state_kv(db_path, worker_name, 'last_error')

    result = {"accepted": True, "status": phase, "worker_name": worker_name, "pid": int(pid_str) if pid_str and pid_str.isdigit() else None, "heartbeat": hb, "db_path": db_path, "truncated": False}
    if sleep_until: result['sleep_until'] = sleep_until
    if retry_next_at: result['retry_next_at'] = retry_next_at
    if process_uid: result['process_uid'] = process_uid
    if process_version: result['process_version'] = process_version
    if last_error: result['last_error'] = last_error[:400]
    return result


def start_or_control(params: dict) -> Dict[str, Any]:
    op = (params or {}).get('operation', 'start')
    try:
        if op == 'start': return start(params)
        elif op == 'stop': return stop(params)
        elif op == 'status': return status(params)
        else:
            return {"accepted": False, "status": "error", "message": f"Invalid operation: {op}", "truncated": False}
    except ValueError as e:
        return {"accepted": False, "status": "error", "message": str(e)[:400], "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Unexpected error: {str(e)[:350]}", "truncated": False}
