
# Status operation (refactored <7KB)

from pathlib import Path
from typing import Any, Dict

from .validators import validate_params
from .api_common import db_path_for_worker, compact_errors_for_status, debug_status_block
from .db import get_state_kv, get_phase
from .api_metrics import compute_metrics_window, parse_metrics_window_minutes


def status(params: dict) -> dict:
    p = validate_params(params)
    worker_name = p['worker_name']
    db_path = db_path_for_worker(worker_name)
    if not Path(db_path).exists():
        return {"accepted": True, "status": "unknown", "worker_name": worker_name,
                "message": "No DB found (worker never started or DB deleted)", "truncated": False}

    phase = get_phase(db_path, worker_name) or 'unknown'
    pid_str = get_state_kv(db_path, worker_name, 'pid')
    hb = get_state_kv(db_path, worker_name, 'heartbeat')
    sleep_until = get_state_kv(db_path, worker_name, 'sleep_until')
    retry_next_at = get_state_kv(db_path, worker_name, 'retry_next_at')
    process_uid = get_state_kv(db_path, worker_name, 'process_uid')
    process_version = get_state_kv(db_path, worker_name, 'process_version')

    result = {"accepted": True, "status": phase, "worker_name": worker_name,
              "pid": int(pid_str) if pid_str and pid_str.isdigit() else None,
              "heartbeat": hb, "db_path": db_path, "truncated": False}
    if sleep_until: result['sleep_until'] = sleep_until
    if retry_next_at: result['retry_next_at'] = retry_next_at
    if process_uid: result['process_uid'] = process_uid
    if process_version: result['process_version'] = process_version

    # Optional compact metrics — only if explicitly requested
    include_metrics = False
    metrics_param = (params or {}).get('metrics') or {}
    include_metrics = bool(params.get('include_metrics')) or bool(metrics_param.get('include'))
    if include_metrics:
        minutes = parse_metrics_window_minutes(metrics_param)
        result['metrics'] = compute_metrics_window(db_path, worker_name, minutes)

    result.update(compact_errors_for_status(db_path, worker_name))
    result.update(debug_status_block(db_path, worker_name))
    return result
