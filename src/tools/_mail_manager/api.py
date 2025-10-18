import time, uuid, sys, subprocess, os, json, signal
from .validators import validate_params
from .graph import build_execution_graph
from .db import get_db_path, set_state_kv, get_state_kv, utcnow_str, set_meta, get_meta

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def _make_job_id() -> str:
    return f"mailmgr_{int(time.time())}_{uuid.uuid4().hex[:6]}"


def _spawn_detached(db_path: str) -> int:
    """
    Lance le runner en tâche de fond et retourne le PID du processus enfant.
    Le runner lira les paramètres depuis la DB (job_state_kv.__global__/params).

    Exécute le module en mode paquet (-m) pour des imports propres et force cwd à la racine projet.
    """
    python = sys.executable or "python3"
    cmd = [python, "-m", "src.tools._mail_manager.runner", db_path]

    if os.name == "nt":
        # Garder le process détaché pour ne pas bloquer le serveur; le stop 'term' ne sera pas disponible (CTRL_BREAK_EVENT nécessite une console attachée)
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            cwd=ROOT_DIR,
        )
    else:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            cwd=ROOT_DIR,
        )
    return p.pid


def _try_kill_posix(pid: int, sig: int) -> bool:
    try:
        os.kill(pid, sig)
        return True
    except Exception:
        return False


def _try_kill_windows(pid: int, mode: str) -> bool:
    # mode in {'kill'} for now; TERM via CTRL events non supporté en detached
    try:
        if mode == 'kill':
            # taskkill /PID <pid> /T /F
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except Exception:
        return False
    return False


def start_or_control(params: dict) -> dict:
    p = validate_params(params or {})
    op = p.get('operation', 'start')

    worker_name = p.get('worker_name')
    db_path = get_db_path(worker_name)

    if op == 'start':
        phase = get_state_kv(db_path, '__global__', 'phase')
        heartbeat = get_state_kv(db_path, '__global__', 'heartbeat')
        ttl_sec = int(p.get('poll_interval_minutes', 10)) * 60 * 3
        if phase in {'running','sleeping'} and heartbeat:
            import datetime as dt
            try:
                t = dt.datetime.strptime(heartbeat, '%Y-%m-%d %H:%M:%S')
                if (dt.datetime.utcnow() - t).total_seconds() < ttl_sec:
                    pid = get_state_kv(db_path, '__global__', 'pid')
                    return {"accepted": False, "status": "conflict", "message": "already running", "db_path": db_path, "phase": phase, "heartbeat": heartbeat, "pid": pid, "truncated": False}
            except Exception:
                pass
        saved_params = {
            'worker_name': worker_name,
            'persona': p.get('persona', ''),
            'mailboxes': p.get('mailboxes', []),
            'folders': p.get('folders', []),
            'poll_interval_minutes': p.get('poll_interval_minutes', 10),
            'mark_read': p.get('mark_read', True),
            'llm_model': p.get('llm_model', 'gpt-5-mini')
        }
        set_state_kv(db_path, '__global__', 'params', json.dumps(saved_params))
        set_state_kv(db_path, '__global__', 'phase', 'starting')
        set_state_kv(db_path, '__global__', 'cancel', 'false')
        set_state_kv(db_path, '__global__', 'heartbeat', utcnow_str())
        set_meta(db_path, 'worker_name', worker_name)
        set_meta(db_path, 'persona', p.get('persona', ''))
        graph = build_execution_graph(); set_state_kv(db_path, '__global__', 'graph_mermaid', graph['mermaid'])

        try:
            pid = _spawn_detached(db_path)
            set_state_kv(db_path, '__global__', 'pid', str(pid))
        except Exception as e:
            set_state_kv(db_path, '__global__', 'phase', 'failed'); set_state_kv(db_path, '__global__', 'last_error', f"spawn_failed: {e}")
            return {"accepted": False, "status": "failed", "message": f"spawn failed: {e}", "db_path": db_path, "truncated": False}

        return {"accepted": True, "status": "starting", "job_id": _make_job_id(), "db_path": db_path, "pid": pid, "graph_mermaid": graph["mermaid"], "heartbeat": get_state_kv(db_path, '__global__', 'heartbeat'), "truncated": False}

    if op == 'stop':
        mode = (p.get('mode') or 'soft').lower()  # 'soft' | 'term' | 'kill'
        set_state_kv(db_path, '__global__', 'cancel', 'true')
        pid_val = get_state_kv(db_path, '__global__', 'pid')
        if not pid_val:
            return {"accepted": True, "status": "ok", "message": "cancel requested (no pid)", "db_path": db_path, "truncated": False}
        try:
            pid = int(pid_val)
        except Exception:
            pid = None
        # Soft only: rely on cooperative cancel
        if mode == 'soft' or not pid:
            return {"accepted": True, "status": "ok", "message": "cancel requested", "db_path": db_path, "truncated": False}
        # TERM (POSIX only)
        if mode == 'term' and os.name != 'nt' and pid:
            ok = _try_kill_posix(pid, signal.SIGTERM)
            if ok:
                set_state_kv(db_path, '__global__', 'last_signal', 'SIGTERM')
                set_state_kv(db_path, '__global__', 'phase', 'canceling')
                return {"accepted": True, "status": "ok", "message": "term sent", "pid": pid, "db_path": db_path}
            return {"accepted": False, "status": "error", "message": "term failed"}
        # KILL (POSIX/Windows)
        if mode == 'kill' and pid:
            if os.name == 'nt':
                ok = _try_kill_windows(pid, 'kill')
            else:
                ok = _try_kill_posix(pid, signal.SIGKILL)
            if ok:
                set_state_kv(db_path, '__global__', 'last_signal', 'KILL')
                set_state_kv(db_path, '__global__', 'phase', 'failed')
                return {"accepted": True, "status": "ok", "message": "killed", "pid": pid, "db_path": db_path}
            return {"accepted": False, "status": "error", "message": "kill failed"}
        return {"accepted": True, "status": "ok", "message": "cancel requested (no action)", "db_path": db_path, "truncated": False}

    if op == 'status':
        phase = get_state_kv(db_path, '__global__', 'phase') or 'unknown'
        pid = get_state_kv(db_path, '__global__', 'pid')
        heartbeat = get_state_kv(db_path, '__global__', 'heartbeat')
        sleep_until = get_state_kv(db_path, '__global__', 'sleep_until')
        worker = get_meta(db_path, 'worker_name')
        persona = get_meta(db_path, 'persona')
        return {"accepted": True, "status": phase, "pid": pid, "worker_name": worker, "persona": persona, "heartbeat": heartbeat, "sleep_until": sleep_until, "db_path": db_path, "truncated": False}

    return {"accepted": False, "status": "error", "message": "invalid operation"}
