#!/usr/bin/env python3
# Runner main (thin): signals + delegates to runner_loop.run_loop
import sys
import os
import signal
from pathlib import Path

# Keep only DB + crash import at top (safe)
from .db import get_state_kv, set_phase, set_state_kv, init_db
from .logging import log_crash

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
    
    try:
        # Init DB first to be able to log any crash
        init_db(_db_path)

        # Derive worker_name
        _worker_name = get_state_kv(_db_path, '__global__', 'worker_name') or ''
        if not _worker_name:
            db_filename = Path(_db_path).stem
            _worker_name = db_filename.replace('worker_', '') if db_filename.startswith('worker_') else '__global__'

        _setup_signals()
        
        # DEFER imports that may fail until after DB init
        from .runner_helpers import load_process
        from .runner_loop import run_loop
        
        worker_file = get_state_kv(_db_path, _worker_name, 'worker_file')
        if not worker_file:
            raise RuntimeError('worker_file not found in DB')
            
        project_root = Path(__file__).resolve().parents[3]
        worker_file_full = project_root / worker_file
        
        process = load_process(str(worker_file_full))
        
        # Inject dynamic worker constants
        worker_ctx = process.get('worker_ctx', {}) or {}
        worker_ctx['worker_name'] = _worker_name
        worker_ctx['db_file'] = f"worker_{_worker_name}.db"
        process['worker_ctx'] = worker_ctx

        graph = process.get('graph', {})
        run_loop(_db_path, _worker_name, worker_ctx, graph, str(worker_file_full))

    except Exception as e:
        # FATAL: persist error and crash log
        try:
            set_phase(_db_path, _worker_name or '__global__', 'failed')
            set_state_kv(_db_path, _worker_name or '__global__', 'last_error', f'Fatal bootstrap error: {str(e)[:300]}')
            log_crash(
                db_path=_db_path,
                worker=_worker_name or '__global__',
                cycle_id="startup",
                node="runner_bootstrap",
                error=e,
                worker_ctx={},
                cycle_ctx={}
            )
        except Exception:
            pass
        print(f"FATAL: Orchestrator runner failed to start: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
