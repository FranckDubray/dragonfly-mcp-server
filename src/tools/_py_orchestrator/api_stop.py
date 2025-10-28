
from __future__ import annotations
import os
import signal
import sys
from .validators import validate_params
from .api_spawn import db_path_for_worker
from .db import get_state_kv, set_state_kv, set_phase


def _to_int(s):
    try:
        return int(s)
    except Exception:
        return None


def _terminate_pid(pid: int, mode: str) -> bool:
    try:
        if sys.platform.startswith('win'):
            # On Windows, os.kill supports SIGTERM but no SIGKILL; best-effort
            if mode == 'kill':
                os.kill(pid, signal.SIGTERM)
                return True
            os.kill(pid, signal.SIGTERM)
            return True
        else:
            if mode == 'kill':
                os.kill(pid, signal.SIGKILL)
                return True
            os.kill(pid, signal.SIGTERM)
            return True
    except Exception:
        return False


def stop(params: dict) -> dict:
    p = validate_params({**params, 'operation': 'stop'})
    wn = p['worker_name']
    mode = (p.get('stop') or {}).get('mode', 'soft')
    dbp = db_path_for_worker(wn)

    if mode == 'soft':
        try:
            set_state_kv(dbp, wn, 'cancel', 'true')
            return {"accepted": True, "status": "ok", "message": "Cancel flag set (cooperative shutdown)", "pid": _to_int(get_state_kv(dbp, wn, 'pid') or '')}
        except Exception as e:
            return {"accepted": False, "status": "error", "message": f"Failed to set cancel flag: {str(e)[:200]}"}

    # term/kill
    pid_s = get_state_kv(dbp, wn, 'pid') or ''
    pid = _to_int(pid_s)
    if not pid:
        return {"accepted": False, "status": "error", "message": "No PID found"}
    ok = _terminate_pid(pid, mode)
    if not ok:
        return {"accepted": False, "status": "error", "message": f"Failed to send {mode} to pid {pid}"}
    try:
        set_phase(dbp, wn, 'canceled')
    except Exception:
        pass
    return {"accepted": True, "status": "ok", "message": f"Signal {mode} sent", "pid": pid}
