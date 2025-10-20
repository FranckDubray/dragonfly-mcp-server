# Runner helpers: state utils, debug state, process loading, hot-reload
from datetime import datetime, timezone
from pathlib import Path
from .db import get_state_kv, set_state_kv, heartbeat
from .process_loader import load_process_with_imports, ProcessLoadError


def utcnow_str() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')


def is_canceled(db_path: str, worker: str) -> bool:
    return get_state_kv(db_path, worker, 'cancel') == 'true'


def cooperative_sleep(db_path: str, worker: str, total_seconds: float, tick: float = 0.5):
    import time
    remaining = total_seconds
    while remaining > 0 and not is_canceled(db_path, worker) and not is_debug_enabled(db_path, worker):
        time.sleep(min(tick, remaining))
        remaining -= tick


def is_debug_enabled(db_path: str, worker: str) -> bool:
    return get_state_kv(db_path, worker, 'debug.enabled') == 'true'


def get_debug_state(db_path: str, worker: str) -> dict:
    import json
    try:
        enabled = get_state_kv(db_path, worker, 'debug.enabled') == 'true'
        mode = get_state_kv(db_path, worker, 'debug.mode') or 'step'
        until = get_state_kv(db_path, worker, 'debug.until')
        breakpoints = get_state_kv(db_path, worker, 'debug.breakpoints')
        return {
            'enabled': enabled,
            'mode': mode,
            'until': (json.loads(until) if until else None),
            'breakpoints': (json.loads(breakpoints) if breakpoints else [])
        }
    except Exception:
        return {'enabled': False}


def load_process(worker_file: str) -> dict:
    try:
        return load_process_with_imports(worker_file)
    except ProcessLoadError as e:
        raise RuntimeError(f"Failed to load process: {e}")


def compute_process_uid(worker_file: str) -> str:
    with open(worker_file, 'rb') as f:
        import hashlib
        return hashlib.sha256(f.read()).hexdigest()[:12]


def check_hot_reload(db_path: str, worker: str, worker_file: str) -> bool:
    hot_reload = get_state_kv(db_path, worker, 'hot_reload')
    if hot_reload != 'true':
        return False
    current_uid = get_state_kv(db_path, worker, 'process_uid')
    new_uid = compute_process_uid(worker_file)
    return current_uid != new_uid
