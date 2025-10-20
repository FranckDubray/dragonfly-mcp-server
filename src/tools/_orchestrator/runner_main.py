#!/usr/bin/env python3
# Runner main (thin): signals + delegates to runner_loop.run_loop
import sys
import os
import signal
from pathlib import Path
from .db import get_state_kv, set_phase, set_state_kv
from .runner_helpers import load_process
from .runner_loop import run_loop

_db_path: str = ""
_worker_name: str = ""

def _signal_handler(signum, frame):
    global _db_path, _worker_name
    if _db_path and _worker_name:
        try:
            from .db import set_state_kv, set_phase
            set_state_kv(_db_path, _worker_name, 'cancel', 'true')
            set_phase(_db_path, _worker_name, 'canceling')
        except Exception:
            pass

def _setup_signals():
    if os.name == 'nt':
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGBREAK, _signal_handler)
    else:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)


def main():
    if len(sys.argv) < 2:
        print("Usage: runner.py <db_path>", file=sys.stderr)
        sys.exit(1)
    global _db_path, _worker_name
    _db_path = sys.argv[1]
    _worker_name = get_state_kv(_db_path, '__global__', 'worker_name') or ''
    if not _worker_name:
        db_filename = Path(_db_path).stem
        _worker_name = db_filename.replace('worker_', '') if db_filename.startswith('worker_') else '__global__'
    _setup_signals()
    worker_file = get_state_kv(_db_path, _worker_name, 'worker_file')
    if not worker_file:
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', 'worker_file not found in DB')
        sys.exit(1)
    project_root = Path(__file__).resolve().parents[3]
    worker_file_full = project_root / worker_file
    try:
        process = load_process(str(worker_file_full))
    except Exception as e:
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', f'Failed to load process: {str(e)[:300]}')
        sys.exit(1)
    worker_ctx = process.get('worker_ctx', {})
    graph = process.get('graph', {})
    run_loop(_db_path, _worker_name, worker_ctx, graph, str(worker_file_full))

if __name__ == '__main__':
    main()
