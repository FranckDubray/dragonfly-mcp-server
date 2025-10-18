#!/usr/bin/env python3
# Orchestrator detached runner (background process)
# Spawned by tool API, runs until EXIT or cancel/error.
# Handles SIGTERM/SIGINT/SIGBREAK for graceful shutdown.

import sys
import os
import signal
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .handlers import bootstrap_handlers
from .engine import OrchestratorEngine

# Global state for signal handlers
_db_path: str = ""
_worker_name: str = ""

def _utcnow_str() -> str:
    """UTC ISO8601 microseconds"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

def _signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT/SIGBREAK → set cancel=true, phase=canceling"""
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
    """Register signal handlers (OS-aware)"""
    if os.name == 'nt':
        # Windows: SIGINT, SIGBREAK
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGBREAK, _signal_handler)
    else:
        # Unix: SIGTERM, SIGINT
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)

def _is_canceled(db_path: str, worker: str) -> bool:
    """Check if cancel flag is set"""
    cancel = get_state_kv(db_path, worker, 'cancel')
    return cancel == 'true'

def _cooperative_sleep(db_path: str, worker: str, total_seconds: float, tick: float = 0.5):
    """Sleep in small ticks, checking cancel flag regularly"""
    remaining = total_seconds
    while remaining > 0 and not _is_canceled(db_path, worker):
        time.sleep(min(tick, remaining))
        remaining -= tick

def _load_process(worker_file: str) -> dict:
    """Load process JSON from worker_file (full path)"""
    with open(worker_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def _compute_process_uid(worker_file: str) -> str:
    """Compute SHA256 hash of worker_file content (short 12 chars)"""
    with open(worker_file, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]

def _check_hot_reload(db_path: str, worker: str, worker_file: str) -> bool:
    """
    Check if process file changed (hot-reload).
    
    Returns:
        True if reload needed, False otherwise
    """
    hot_reload = get_state_kv(db_path, worker, 'hot_reload')
    if hot_reload != 'true':
        return False
    
    current_uid = get_state_kv(db_path, worker, 'process_uid')
    new_uid = _compute_process_uid(worker_file)
    
    return current_uid != new_uid

def _run_loop(db_path: str, worker: str, worker_ctx: dict, graph: dict, worker_file: str):
    """Main loop: START → cycle → EXIT or sleep → repeat"""
    
    # Bootstrap handlers (with cancel_flag_fn for sleep)
    cancel_flag_fn = lambda: _is_canceled(db_path, worker)
    bootstrap_handlers(cancel_flag_fn)
    
    # Create engine
    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn)
    
    cycle_ctx = {}  # Empty cycle context (reset each cycle)
    cycle_num = 0
    
    while not _is_canceled(db_path, worker):
        # Hot-reload check (before each cycle)
        if _check_hot_reload(db_path, worker, worker_file):
            print(f"[runner] Hot-reload detected, reloading process...", file=sys.stderr)
            try:
                process = _load_process(worker_file)
                worker_ctx = process.get('worker_ctx', {})
                graph = process.get('graph', {})
                
                # Update engine with new graph
                engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn)
                
                # Update process_uid in DB
                new_uid = _compute_process_uid(worker_file)
                set_state_kv(db_path, worker, 'process_uid', new_uid)
                
                print(f"[runner] Process reloaded (new uid: {new_uid})", file=sys.stderr)
            except Exception as e:
                print(f"[runner] Hot-reload failed: {e}, continuing with old process", file=sys.stderr)
        
        cycle_num += 1
        cycle_id = f"cycle_{cycle_num:03d}"
        
        # Set phase=running, clear sleep_until
        set_phase(db_path, worker, 'running')
        set_state_kv(db_path, worker, 'sleep_until', '')
        set_state_kv(db_path, worker, 'retry_next_at', '')
        heartbeat(db_path, worker)
        
        print(f"[runner] Starting {cycle_id}", file=sys.stderr)
        
        # Execute one cycle (via engine)
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx)
        except Exception as e:
            # Fatal error: log and exit
            print(f"[runner] Fatal error in {cycle_id}: {e}", file=sys.stderr)
            set_phase(db_path, worker, 'failed')
            set_state_kv(db_path, worker, 'last_error', str(e)[:400])
            heartbeat(db_path, worker)
            return
        
        print(f"[runner] Completed {cycle_id}", file=sys.stderr)
        
        # Check if EXIT was reached
        if exit_reached:
            print(f"[runner] EXIT node reached, stopping worker", file=sys.stderr)
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return
        
        # Check cancel after cycle
        if _is_canceled(db_path, worker):
            break
        
        # Get sleep_seconds from worker_ctx (if not set, exit after one cycle)
        sleep_seconds = worker_ctx.get('sleep_seconds', None)
        
        if sleep_seconds is None or sleep_seconds == 0:
            # No sleep configured → one-shot execution, exit
            print(f"[runner] No sleep configured, exiting after one cycle", file=sys.stderr)
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return
        
        # Set phase=sleeping, sleep
        set_phase(db_path, worker, 'sleeping')
        sleep_until = (datetime.now(timezone.utc) + timedelta(seconds=sleep_seconds))
        set_state_kv(db_path, worker, 'sleep_until', sleep_until.strftime('%Y-%m-%d %H:%M:%S.%f'))
        heartbeat(db_path, worker)
        
        print(f"[runner] Sleeping {sleep_seconds}s (until {sleep_until.strftime('%H:%M:%S')})", file=sys.stderr)
        _cooperative_sleep(db_path, worker, sleep_seconds)
    
    # Exited loop: set phase=canceled
    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
    print(f"[runner] Exited gracefully after {cycle_num} cycles", file=sys.stderr)

def main():
    """Main entry: parse args, setup signals, load process, run loop"""
    global _db_path, _worker_name
    
    if len(sys.argv) < 2:
        print("Usage: runner.py <db_path>", file=sys.stderr)
        sys.exit(1)
    
    _db_path = sys.argv[1]
    
    # Read worker_name from DB
    # (We use __global__ as default namespace for now; API writes to worker_name key)
    _worker_name = get_state_kv(_db_path, '__global__', 'worker_name')
    if not _worker_name:
        # Fallback: extract from db_path filename (worker_<name>.db)
        db_filename = Path(_db_path).stem  # e.g., "worker_test"
        _worker_name = db_filename.replace('worker_', '') if db_filename.startswith('worker_') else '__global__'
    
    print(f"[runner] Starting runner for worker '{_worker_name}' (db: {_db_path})", file=sys.stderr)
    
    # Setup signal handlers
    _setup_signals()
    
    # Read worker_file from DB
    worker_file = get_state_kv(_db_path, _worker_name, 'worker_file')
    if not worker_file:
        print("[runner] ERROR: worker_file not found in DB", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', 'worker_file not found in DB')
        sys.exit(1)
    
    # Resolve worker_file (relative to project root)
    project_root = Path(__file__).resolve().parents[3]
    worker_file_full = project_root / worker_file
    
    if not worker_file_full.is_file():
        print(f"[runner] ERROR: worker_file not found: {worker_file_full}", file=sys.stderr)
        set_phase(_db_path, _worker_name, 'failed')
        set_state_kv(_db_path, _worker_name, 'last_error', f'worker_file not found: {worker_file}')
        sys.exit(1)
    
    # Load process JSON
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
    
    # Run loop (until EXIT, cancel or fatal error)
    _run_loop(_db_path, _worker_name, worker_ctx, graph, str(worker_file_full))

if __name__ == '__main__':
    main()
