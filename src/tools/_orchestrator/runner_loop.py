
























# Runner loop: executes the JSON FSM with debug integration (refactored <7KB)
from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .handlers import bootstrap_handlers
# IMPORTANT: import OrchestratorEngine directly from the module to avoid engine/__init__ side-effects
from .engine.orchestrator import OrchestratorEngine
from .runner_helpers import (
    is_canceled, is_debug_enabled, get_debug_state,
    load_process, compute_process_uid, check_hot_reload,
)
from .debug_loop import debug_wait_loop
from .utils import utcnow_str


def _persist_debug_pause(db_path: str, worker: str, cycle_id: str, last_step: dict, next_node: str) -> None:
    """Persist debug pause state to DB."""
    import json
    # NEW: keep previous paused_at as previous_node for better UI
    try:
        prev_paused = get_state_kv(db_path, worker, 'debug.paused_at') or ''
        if prev_paused:
            set_state_kv(db_path, worker, 'debug.previous_node', prev_paused)
    except Exception:
        pass

    set_phase(db_path, worker, 'debug_paused')
    set_state_kv(db_path, worker, 'debug.cycle_id', cycle_id)
    paused_at = last_step.get('node') or ''
    set_state_kv(db_path, worker, 'debug.paused_at', paused_at)
    set_state_kv(db_path, worker, 'debug.next_node', next_node or '')
    set_state_kv(db_path, worker, 'debug.last_step', json.dumps(last_step))
    # Mark pause hook for observability
    set_state_kv(db_path, worker, 'debug.pause_hook', 'paused')
    # Handshake for sync wait
    req_id = get_state_kv(db_path, worker, 'debug.req_id') or ''
    set_state_kv(db_path, worker, 'debug.response_id', req_id)
    heartbeat(db_path, worker)


def _clear_debug_state(db_path: str, worker: str) -> None:
    """Clear ephemeral debug state before resuming."""
    set_state_kv(db_path, worker, 'debug.paused_at', '')
    set_state_kv(db_path, worker, 'debug.last_step', '')
    # keep ctx_diff intact until next pause is computed; it will be overwritten at next pause
    set_state_kv(db_path, worker, 'debug.executing_node', '')


def _handle_debug_pause_loop(
    db_path: str, worker: str, engine: OrchestratorEngine,
    cycle_id: str, worker_ctx: dict, cycle_ctx: dict,
    initial_pause: 'DebugPause', initial_start_from: str = None
) -> bool:
    """
    Unified debug pause handler - works for both immediate and mid-cycle pauses.
    
    Returns:
        bool: True if EXIT reached, False if cycle completed normally
    """
    from .engine.debug_utils import DebugPause
    import json
    
    # Persist initial pause with actual ctx diff
    last_step = engine.get_last_step() or {}
    last_diff = engine.get_last_ctx_diff() or {"added": {}, "changed": {}, "deleted": []}
    set_state_kv(db_path, worker, 'debug.ctx_diff', json.dumps(last_diff))
    _persist_debug_pause(db_path, worker, cycle_id, last_step, initial_pause.next_node or '')
    
    # Loop: wait for command, execute, pause again if needed
    while True:
        debug_wait_loop(db_path, worker)
        
        # Check if debug was disabled
        if not is_debug_enabled(db_path, worker):
            break
        
        # Get start_from node
        start_from = get_state_kv(db_path, worker, 'debug.next_node') or initial_pause.next_node
        
        # Resume execution
        _clear_debug_state(db_path, worker)
        set_phase(db_path, worker, 'running')
        heartbeat(db_path, worker)
        
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from_node=start_from)
            # Cycle completed without pause
            return exit_reached
            
        except DebugPause as e:
            # Another pause - persist and loop with real diff
            last_step = engine.get_last_step() or {}
            last_diff = engine.get_last_ctx_diff() or {"added": {}, "changed": {}, "deleted": []}
            set_state_kv(db_path, worker, 'debug.ctx_diff', json.dumps(last_diff))
            _persist_debug_pause(db_path, worker, cycle_id, last_step, e.next_node or '')
            # Continue loop to wait for next step
            
        except Exception as e:
            set_phase(db_path, worker, 'failed')
            set_state_kv(db_path, worker, 'last_error', str(e)[:400])
            heartbeat(db_path, worker)
            raise
    
    # Debug was disabled, return to normal flow
    return False


def run_loop(db_path: str, worker: str, worker_ctx: dict, graph: dict, worker_file: str):
    """Main execution loop (START → … → END/EXIT), with unified debug integration."""
    cancel_flag_fn = lambda: is_canceled(db_path, worker)
    
    try:
        bootstrap_handlers(cancel_flag_fn)
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'bootstrap_handlers: {str(e)[:200]}')
        heartbeat(db_path, worker)
        return

    engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, lambda: get_debug_state(db_path, worker))
    cycle_ctx = {}
    cycle_num = 1
    cycle_id = f"cycle_{cycle_num:03d}"

    from .engine.debug_utils import DebugPause

    while not is_canceled(db_path, worker):
        # Hot-reload check (disabled in debug mode)
        if not is_debug_enabled(db_path, worker) and check_hot_reload(db_path, worker, worker_file):
            try:
                process = load_process(worker_file)
                worker_ctx = process.get('worker_ctx', {})
                graph = process.get('graph', {})
                engine = OrchestratorEngine(graph, db_path, worker, cancel_flag_fn, lambda: get_debug_state(db_path, worker))
                new_uid = compute_process_uid(worker_file)
                set_state_kv(db_path, worker, 'process_uid', new_uid)
            except Exception:
                pass

        # Handle immediate pause at START if requested
        start_from = None
        if is_debug_enabled(db_path, worker) and (get_state_kv(db_path, worker, 'debug.pause_request') or '') == 'immediate':
            # For observability, mark the hook
            set_state_kv(db_path, worker, 'debug.pause_hook', 'immediate_requested')
            start_node = (engine.find_start() or {}).get('name', 'START')
            # Create fake DebugPause for START
            fake_pause = DebugPause(start_node)
            fake_pause.next_node = start_node
            set_state_kv(db_path, worker, 'debug.pause_request', '')
            set_state_kv(db_path, worker, 'debug.pause_hook', 'immediate_consumed')
            
            # Use unified handler
            try:
                exit_reached = _handle_debug_pause_loop(
                    db_path, worker, engine, cycle_id, worker_ctx, cycle_ctx, fake_pause, start_node
                )
                if exit_reached:
                    set_state_kv(db_path, worker, 'last_error', '')
                    set_phase(db_path, worker, 'completed')
                    heartbeat(db_path, worker)
                    return
                # Cycle completed, continue to next
                cycle_num += 1
                cycle_id = f"cycle_{cycle_num:03d}"
                continue
            except Exception:
                return  # Already handled by _handle_debug_pause_loop

        # Normal execution (may be interrupted by DebugPause)
        set_phase(db_path, worker, 'running')
        set_state_kv(db_path, worker, 'sleep_until', '')
        set_state_kv(db_path, worker, 'retry_next_at', '')
        heartbeat(db_path, worker)
        
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from)
            
        except DebugPause as e:
            # Debug pause mid-cycle - use unified handler
            try:
                exit_reached = _handle_debug_pause_loop(
                    db_path, worker, engine, cycle_id, worker_ctx, cycle_ctx, e
                )
            except Exception:
                return  # Already handled
        
        except Exception as e:
            set_phase(db_path, worker, 'failed')
            set_state_kv(db_path, worker, 'last_error', str(e)[:400])
            heartbeat(db_path, worker)
            return

        if exit_reached:
            set_state_kv(db_path, worker, 'last_error', '')
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return

        # END handled in engine (reloop to START). Increment for new external cycle.
        cycle_num += 1
        cycle_id = f"cycle_{cycle_num:03d}"

        if is_canceled(db_path, worker):
            break

    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
