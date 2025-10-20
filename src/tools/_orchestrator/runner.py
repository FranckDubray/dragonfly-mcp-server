#!/usr/bin/env python3
# Orchestrator detached runner (background process)

import sys
import os
import signal
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .handlers import bootstrap_handlers
from .engine import OrchestratorEngine
from .process_loader import load_process_with_imports, ProcessLoadError

_db_path: str = ""
_worker_name: str = ""

def _utcnow_str() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

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

def _is_canceled(db_path: str, worker: str) -> bool:
    cancel = get_state_kv(db_path, worker, 'cancel')
    return cancel == 'true'

def _cooperative_sleep(db_path: str, worker: str, total_seconds: float, tick: float = 0.5):
    remaining = total_seconds
    while remaining > 0 and not _is_canceled(db_path, worker) and not _is_debug_enabled(db_path, worker):
        time.sleep(min(tick, remaining))
        remaining -= tick

def _is_debug_enabled(db_path: str, worker: str) -> bool:
    return (get_state_kv(db_path, worker, 'debug.enabled') == 'true')

def _get_debug_state(db_path: str, worker: str) -> dict:
    try:
        enabled = get_state_kv(db_path, worker, 'debug.enabled') == 'true'
        mode = get_state_kv(db_path, worker, 'debug.mode') or 'step'
        until = get_state_kv(db_path, worker, 'debug.until')
        breakpoints = get_state_kv(db_path, worker, 'debug.breakpoints')
        import json
        return {
            'enabled': enabled,
            'mode': mode,
            'until': json.loads(until) if until else None,
            'breakpoints': json.loads(breakpoints) if breakpoints else []
        }
    except Exception:
        return {'enabled': False}

def _run_loop(db_path: str, worker: str, worker_ctx: dict, graph: dict, worker_file: str):
    cancel_flag_fn = lambda: _is_canceled(db_path, worker)
    try:
        bootstrap_handlers(cancel_flag_fn)
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'bootstrap_handlers: {str(e)[:200]}')
        heartbeat(db_path, worker)
        print(f"[runner] bootstrap failed: {e}", file=sys.stderr)
        return

    # Debug getter wired into engine
    def debug_getter():
        return _get_debug_state(db_path, worker)

    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, debug_getter)
    cycle_ctx = {}
    cycle_num = 0

    while not _is_canceled(db_path, worker):
        # Hot-reload disabled during debug
        if not _is_debug_enabled(db_path, worker):
            if _check_hot_reload(db_path, worker, worker_file):
                print(f"[runner] Hot-reload detected, reloading process...", file=sys.stderr)
                try:
                    process = _load_process(worker_file)
                    worker_ctx = process.get('worker_ctx', {})
                    graph = process.get('graph', {})
                    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, debug_getter)
                    new_uid = _compute_process_uid(worker_file)
                    set_state_kv(db_path, worker, 'process_uid', new_uid)
                    print(f"[runner] Process reloaded (new uid: {new_uid})", file=sys.stderr)
                except Exception as e:
                    print(f"[runner] Hot-reload failed: {e}, continuing with old process", file=sys.stderr)

        cycle_num += 1
        cycle_id = f"cycle_{cycle_num:03d}"
        set_phase(db_path, worker, 'running')
        set_state_kv(db_path, worker, 'sleep_until', '')
        set_state_kv(db_path, worker, 'retry_next_at', '')
        heartbeat(db_path, worker)
        print(f"[runner] Starting {cycle_id}", file=sys.stderr)

        start_from: str | None = None
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from)
        except Exception as e:
            # Debug pause requested?
            from .engine.debug_utils import DebugPause
            if isinstance(e, DebugPause):
                # Persist debug snapshot
                last_step = engine.get_last_step() or {}
                ctx_diff = engine.get_last_ctx_diff() or {"added": {}, "changed": {}, "deleted": []}
                import json
                set_phase(db_path, worker, 'debug_paused')
                set_state_kv(db_path, worker, 'debug.cycle_id', cycle_id)
                set_state_kv(db_path, worker, 'debug.paused_at', last_step.get('node') or '')
                set_state_kv(db_path, worker, 'debug.next_node', e.next_node or '')
                set_state_kv(db_path, worker, 'debug.last_step', json.dumps(last_step))
                set_state_kv(db_path, worker, 'debug.ctx_diff', json.dumps(ctx_diff))
                # NEW: handshake response id
                req_id = get_state_kv(db_path, worker, 'debug.req_id') or ''
                set_state_kv(db_path, worker, 'debug.response_id', req_id)
                heartbeat(db_path, worker)
                print(f"[runner] Debug paused at {last_step.get('node')} → next {e.next_node}", file=sys.stderr)
                # Wait for next command
                _debug_wait_loop(db_path, worker)
                # After step/continue, resume from next_node
                start_from = get_state_kv(db_path, worker, 'debug.next_node') or e.next_node
                # Clear pause marks
                set_state_kv(db_path, worker, 'debug.paused_at', '')
                set_state_kv(db_path, worker, 'debug.last_step', '')
                set_state_kv(db_path, worker, 'debug.ctx_diff', '')
                set_phase(db_path, worker, 'running')
                heartbeat(db_path, worker)
                # Retry current cycle continuing from start_from
                try:
                    exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from_node=start_from)
                except DebugPause as e2:
                    # Re-enter pause path next loop iteration
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
            # Clear stale last_error on successful cycle
            set_state_kv(db_path, worker, 'last_error', '')
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return

        if _is_canceled(db_path, worker):
            break
        sleep_seconds = worker_ctx.get('sleep_seconds', None)
        if sleep_seconds is None or sleep_seconds == 0:
            print(f"[runner] No sleep configured, exiting after one cycle", file=sys.stderr)
            # Clear stale last_error on successful cycle
            set_state_kv(db_path, worker, 'last_error', '')
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return
        set_phase(db_path, worker, 'sleeping')
        sleep_until = (datetime.now(timezone.utc) + timedelta(seconds=sleep_seconds))
        set_state_kv(db_path, worker, 'sleep_until', sleep_until.strftime('%Y-%m-%d %H:%M:%S.%f'))
        # Clear stale last_error at end of successful cycle before sleeping
        set_state_kv(db_path, worker, 'last_error', '')
        heartbeat(db_path, worker)
        print(f"[runner] Sleeping {sleep_seconds}s (until {sleep_until.strftime('%H:%M:%S')})", file=sys.stderr)
        _cooperative_sleep(db_path, worker, sleep_seconds)

    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
    print(f"[runner] Exited gracefully after {cycle_num} cycles", file=sys.stderr)

# === Debug helpers ===

def _debug_wait_loop(db_path: str, worker: str):
    """Busy-wait (with heartbeat) until a debug command arrives, then perform state transitions."""
    last_beat = 0
    import time, json
    while True:
        cmd = get_state_kv(db_path, worker, 'debug.command') or 'none'
        now = time.time()
        if now - last_beat > 10:
            heartbeat(db_path, worker)
            last_beat = now
        if cmd == 'none':
            time.sleep(0.25)
            continue
        if cmd in ('step','continue','run_until'):
            # switch mode
            set_state_kv(db_path, worker, 'debug.mode', 'step' if cmd=='step' else ('continue' if cmd=='continue' else 'until'))
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'disable':
            set_state_kv(db_path, worker, 'debug.enabled', 'false')
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'break_clear':
            set_state_kv(db_path, worker, 'debug.breakpoints', '[]')
            set_state_kv(db_path, worker, 'debug.command', 'none')
        # break_add, break_remove handled by tool API writing breakpoints JSON
        time.sleep(0.1)

# Reuse helpers from previous version

def _load_process(worker_file: str) -> dict:
    try:
        return load_process_with_imports(worker_file)
    except ProcessLoadError as e:
        raise RuntimeError(f"Failed to load process: {e}")

def _compute_process_uid(worker_file: str) -> str:
    with open(worker_file, 'rb') as f:
        import hashlib
        return hashlib.sha256(f.read()).hexdigest()[:12]

def _check_hot_reload(db_path: str, worker: str, worker_file: str) -> bool:
    hot_reload = get_state_kv(db_path, worker, 'hot_reload')
    if hot_reload != 'true':
        return False
    current_uid = get_state_kv(db_path, worker, 'process_uid')
    new_uid = _compute_process_uid(worker_file)
    return current_uid != new_uid


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
        process = _load_process(str(worker_file_full))
    except Exception as e:
        print(f"[runner] ERROR: failed to load process: {e}", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', f'Failed to load process: {str(e)[:300]}')
        sys.exit(1)
    worker_ctx = process.get('worker_ctx', {})
    graph = process.get('graph', {})
    print(f"[runner] Process loaded (version: {process.get('process_version', 'N/A')})", file=sys.stderr)
    _run_loop(_db_path, _worker_name, worker_ctx, graph, str(worker_file_full))

if __name__ == '__main__':
    main()
