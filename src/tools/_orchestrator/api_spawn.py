# API spawn helpers - Process spawning and lifecycle (<2KB)

import subprocess
import sys
import os
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SQLITE_DIR = PROJECT_ROOT / 'sqlite3'
LOG_DIR = PROJECT_ROOT / 'logs'


def compute_process_uid(worker_file_resolved: str) -> str:
    """Compute SHA256 hash of process file for versioning."""
    with open(worker_file_resolved, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def db_path_for_worker(worker_name: str) -> str:
    """Get DB path for worker (creates parent directory if needed)."""
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    return str(SQLITE_DIR / f"worker_{worker_name}.db")


def spawn_runner(db_path: str, worker_name: str) -> int:
    """
    Spawn detached runner process.
    
    Returns:
        PID of spawned process
    """
    cmd = [sys.executable, '-m', 'src.tools._orchestrator.runner', db_path]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"worker_{worker_name}.log"
    log_fh = open(log_path, 'ab', buffering=0)
    
    if os.name == 'nt':
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), creationflags=flags,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    else:
        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), start_new_session=True,
                                stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh)
    return proc.pid
