
import subprocess
import sys
from pathlib import Path
from .api_common import PROJECT_ROOT, SQLITE_DIR, LOG_DIR


def db_path_for_worker(worker_name: str) -> str:
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    return str(SQLITE_DIR / f"worker_{worker_name}.db")


def spawn_runner(db_path: str, worker_name: str) -> int:
    """Spawn detached runner process for Python orchestrator."""
    cmd = [sys.executable, '-m', 'src.tools._py_orchestrator.runner', db_path]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"worker_{worker_name}.log"
    log_fh = open(log_path, 'ab', buffering=0)

    if sys.platform.startswith('win'):
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), creationflags=flags,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    else:
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), start_new_session=True,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    return proc.pid
