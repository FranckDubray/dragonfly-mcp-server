#! /usr/bin/env python3
import sys
from pathlib import Path
from .db import init_db, get_state_kv, set_state_kv, set_phase
from src.tools._orchestrator.utils.time import utcnow_str
from .runner_loop import run_loop
from .runner_parts.run_audit import persist_run_audit

_db_path = ""
_worker_name = ""

def main():
    global _db_path, _worker_name
    if len(sys.argv) < 2:
        print("Usage: runner.py <db_path>", file=sys.stderr)
        sys.exit(1)
    _db_path = sys.argv[1]
    init_db(_db_path)
    _worker_name = get_state_kv(_db_path, '__global__', 'worker_name') or ''
    if not _worker_name:
        db_filename = Path(_db_path).stem
        _worker_name = db_filename.replace('worker_', '') if db_filename.startswith('worker_') else '__global__'
    try:
        set_phase(_db_path, _worker_name, 'starting')
        run_loop(_db_path, _worker_name)
    except Exception as e:
        try:
            set_phase(_db_path, _worker_name, 'failed')
            set_state_kv(_db_path, _worker_name, 'last_error', str(e)[:400])
        except Exception:
            pass
        print(f"FATAL: Py Orchestrator runner failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Persist run audit regardless of outcome (completed/failed/canceled)
        try:
            phase = get_state_kv(_db_path, _worker_name, 'phase') or ''
            persist_run_audit(_db_path, _worker_name, status=phase)
        except Exception:
            pass

if __name__ == '__main__':
    main()
