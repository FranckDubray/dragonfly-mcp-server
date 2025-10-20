#!/usr/bin/env python3
# Runner main: signals, loop, debug integration
import sys
import os
import signal
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .handlers import bootstrap_handlers
from .engine import OrchestratorEngine
from .runner_helpers import (
    utcnow_str, is_canceled, is_debug_enabled, get_debug_state,
    load_process, compute_process_uid, check_hot_reload,
)
from .debug_loop import debug_wait_loop

_db_path: str = ""
_worker_name: str = ""

def _signal_handler(signum, frame):
    global _db_path, _worker_name
    if _db_path and _worker_name:
        try:
            set_state_kv(_db_path, _worker_name, 'cancel', 'true')
            set_phase(_db_path, _worker_name, 'canceling')
            set_state_kv(_db_path, _worker_name, 'last_signal', signal.Signals(signum).name)
            print(f"[runner] Signal {signal.Signals(signum).name} received, cancel flag set", file=sys.stderr)
        except Exception as e:
            print(f"[runner] Error setting cancel flag: {e}", file=sys.stderr)

def _setup_signals():
    if os.name == 'nt':
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGBREAK, _signal_handler)
    else:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)


def run_loop(db_path: str, worker: str, worker_ctx: dict, graph: dict, worker_file: str):
    cancel_flag_fn = lambda: is_canceled(db_path, worker)
    try:
        bootstrap_handlers(cancel_flag_fn)
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'bootstrap_handlers: {str(e)[:200]}')
        heartbeat(db_path, worker)
        print(f"[runner] bootstrap failed: {e}", file=sys.stderr)
        return

    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, lambda: get_debug_state(db_path, worker))
    cycle_ctx = {}
    cycle_num = 1
    cycle_id = f"cycle_{cycle_num:03d}"

    while not is_canceled(db_path, worker):
        # Hot-reload disabled during debug
        if not is_debug_enabled(db_path, worker):
            if check_hot_reload(db_path, worker, worker_file):
                print(f"[runner] Hot-reload detected, reloading process...", file=sys.stderr)
                try:
                    process = load_process(worker_file)
                    worker_ctx = process.get('worker_ctx', {})
                    graph = process.get('graph', {})
                    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, lambda: get_debug_state(db_path, worker))
                    new_uid = compute_process_uid(worker_file)
                    set_state_kv(db_path, worker, 'process_uid', new_uid)
                    print(f"[runner] Process reloaded (new uid: {new_uid})", file=sys.stderr)
                except Exception as e:
                    print(f"[runner] Hot-reload failed: {e}, continuing with old process", file=sys.stderr)

        set_phase(db_path, worker, 'running')
        set_state_kv(db_path, worker, 'sleep_until', '')
        set_state_kv(db_path, worker, 'retry_next_at', '')
        heartbeat(db_path, worker)
        print(f"[runner] Starting {cycle_id}", file=sys.stderr)

        start_from = None
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from)
        except Exception as e:
            from .engine.debug_utils import DebugPause
            if isinstance(e, DebugPause):
                last_step = engine.get_last_step() or {}
                ctx_diff = engine.get_last_ctx_diff() or {"added": {}, "changed": {}, "deleted": []}
                import json
                set_phase(db_path, worker, 'debug_paused')
                set_state_kv(db_path, worker, 'debug.cycle_id', cycle_id)
                set_state_kv(db_path, worker, 'debug.paused_at', last_step.get('node') or '')
                set_state_kv(db_path, worker, 'debug.next_node', e.next_node or '')
                set_state_kv(db_path, worker, 'debug.last_step', json.dumps(last_step))
                set_state_kv(db_path, worker, 'debug.ctx_diff', json.dumps(ctx_diff))
                req_id = get_state_kv(db_path, worker, 'debug.req_id') or ''
                set_state_kv(db_path, worker, 'debug.response_id', req_id)
                heartbeat(db_path, worker)
                print(f"[runner] Debug paused at {last_step.get('node')} → next {e.next_node}", file=sys.stderr)
                debug_wait_loop(db_path, worker)
                # Resume same cycle
                start_from = get_state_kv(db_path, worker, 'debug.next_node') or e.next_node
                set_state_kv(db_path, worker, 'debug.paused_at', '')
                set_state_kv(db_path, worker, 'debug.last_step', '')
                set_state_kv(db_path, worker, 'debug.ctx_diff', '')
                set_phase(db_path, worker, 'running')
                heartbeat(db_path, worker)
                try:
                    exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from_node=start_from)
                except DebugPause:
                    continue
                except Exception as e2:
                    print(f"[runner] Fatal error in {cycle_id}: {e2}", file=sys.stderr)
                    set_phase(db_path, worker, 'failed')
                    set_state_kv(db_path, worker, 'last_error', str(e2)[:400])
                    heartbeat(db_path, worker)
                    return
            else:
                print(f"[runner] Fatal error in {cycle_id}: {e}", file=sys.stderr)
                set_phase(db_path, worker, 'failed')
                set_state_kv(db_path, worker, 'last_error', str(e)[:400])
                heartbeat(db_path, worker)
                return

        print(f"[runner] Completed {cycle_id}", file=sys.stderr)
        if exit_reached:
            print(f"[runner] EXIT node reached, stopping worker", file=sys.stderr)
            set_state_kv(db_path, worker, 'last_error', '')
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return

        # END handled inside engine: reboucle to START internally.
        # Increment cycle_id only after a full cycle completes and a new one starts intentionally.
        cycle_num += 1
        cycle_id = f"cycle_{cycle_num:03d}"

        if is_canceled(db_path, worker):
            break

    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
    print(f"[runner] Exited gracefully after {cycle_num} cycles", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: runner.py <db_path>", file=sys.stderr)
        sys.exit(1)
    global _db_path, _worker_name
    _db_path = sys.argv[1]
    _worker_name = get_state_kv(_db_path, '__global__', 'worker_name')
    if not _worker_name:
        db_filename = Path(_db_path).stem
        _worker_name = db_filename.replace('worker_', '') if db_filename.startswith('worker_') else '__global__'
    print(f"[runner] Starting runner for worker '{_worker_name}' (db: {_db_path})", file=sys.stderr)
    _setup_signals()
    worker_file = get_state_kv(_db_path, _worker_name, 'worker_file')
    if not worker_file:
        print("[runner] ERROR: worker_file not found in DB", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', 'worker_file not found in DB')
        sys.exit(1)
    project_root = Path(__file__).resolve().parents[3]
    worker_file_full = project_root / worker_file
    if not worker_file_full.is_file():
        print(f"[runner] ERROR: worker_file not found: {worker_file_full}", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', f'worker_file not found: {worker_file}')
        sys.exit(1)
    try:
        process = load_process(str(worker_file_full))
    except Exception as e:
        print(f"[runner] ERROR: failed to load process: {e}", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', f'Failed to load process: {str(e)[:300]}')
        sys.exit(1)
    worker_ctx = process.get('worker_ctx', {})
    graph = process.get('graph', {})
    print(f"[runner] Process loaded (version: {process.get('process_version', 'N/A')})", file=sys.stderr)
    run_loop(_db_path, _worker_name, worker_ctx, graph, str(worker_file_full))

if __name__ == '__main__':
    main()
