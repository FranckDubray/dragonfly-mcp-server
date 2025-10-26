
# Stop operation (split from api_start_stop)

from pathlib import Path
from .validators import validate_params
from .api_common import db_path_for_worker
from .db import get_state_kv, set_state_kv, set_phase


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
            if os.name == 'nt':
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            else:
                os.kill(pid, signal.SIGTERM)
            set_state_kv(db_path, worker_name, 'last_signal', 'SIGTERM')
            set_phase(db_path, worker_name, 'canceling')
            message = "SIGTERM sent"
        elif mode == 'kill':
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=False)
            else:
                os.kill(pid, signal.SIGKILL)
            set_state_kv(db_path, worker_name, 'last_signal', 'SIGKILL')
            set_phase(db_path, worker_name, 'failed')
            message = "SIGKILL sent (force kill)"
        else:
            return {"accepted": False, "status": "error", "message": f"Unknown mode: {mode}", "truncated": False}
        return {"accepted": True, "status": "ok", "message": message, "pid": pid, "db_path": db_path, "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Failed to send signal: {str(e)[:200]}", "pid": pid, "db_path": db_path, "truncated": False}
