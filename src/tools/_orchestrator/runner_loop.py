# Runner loop: executes the JSON FSM with debug integration (kept <7KB)
from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .handlers import bootstrap_handlers
from .engine import OrchestratorEngine
from .runner_helpers import (
    is_canceled, is_debug_enabled, get_debug_state,
    load_process, compute_process_uid, check_hot_reload,
)
from .debug_loop import debug_wait_loop


def _persist_debug_pause(db_path: str, worker: str, cycle_id: str, last_step: dict, next_node: str) -> None:
    import json
    set_phase(db_path, worker, 'debug_paused')
    set_state_kv(db_path, worker, 'debug.cycle_id', cycle_id)
    set_state_kv(db_path, worker, 'debug.paused_at', last_step.get('node') or '')
    set_state_kv(db_path, worker, 'debug.next_node', next_node or '')
    set_state_kv(db_path, worker, 'debug.last_step', json.dumps(last_step))
    # Fallback in-progress visibility
    set_state_kv(db_path, worker, 'debug.executing_node', next_node or '')
    req_id = get_state_kv(db_path, worker, 'debug.req_id') or ''
    set_state_kv(db_path, worker, 'debug.response_id', req_id)
    heartbeat(db_path, worker)


def _resume_after_pause(db_path: str, worker: str, engine: OrchestratorEngine,
                        cycle_id: str, worker_ctx: dict, cycle_ctx: dict, start_from: str) -> bool:
    from .engine.debug_utils import DebugPause
    set_state_kv(db_path, worker, 'debug.paused_at', '')
    set_state_kv(db_path, worker, 'debug.last_step', '')
    set_state_kv(db_path, worker, 'debug.ctx_diff', '')
    set_state_kv(db_path, worker, 'debug.executing_node', '')
    set_phase(db_path, worker, 'running')
    heartbeat(db_path, worker)
    try:
        return engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, start_from_node=start_from)
    except DebugPause:
        # handled by caller
        raise


def run_loop(db_path: str, worker: str, worker_ctx: dict, graph: dict, worker_file: str):
    """Main execution loop (START → … → END/EXIT), with debug integration."""
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
        # Hot-reload off in debug
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

        # Immediate debug pause at START?
        if is_debug_enabled(db_path, worker) and (get_state_kv(db_path, worker, 'debug.pause_request') or '') == 'immediate':
            start_node = (engine.find_start() or {}).get('name', 'START')
            _persist_debug_pause(db_path, worker, cycle_id, {"node": "START", "type": "start"}, start_node)
            debug_wait_loop(db_path, worker)
            start_from = get_state_kv(db_path, worker, 'debug.next_node') or start_node
            set_state_kv(db_path, worker, 'debug.pause_request', '')
            try:
                exit_reached = _resume_after_pause(db_path, worker, engine, cycle_id, worker_ctx, cycle_ctx, start_from)
            except DebugPause as e:
                last_step = engine.get_last_step() or {}
                _persist_debug_pause(db_path, worker, cycle_id, last_step, e.next_node or '')
                debug_wait_loop(db_path, worker)
                start_from = get_state_kv(db_path, worker, 'debug.next_node') or e.next_node
                try:
                    exit_reached = _resume_after_pause(db_path, worker, engine, cycle_id, worker_ctx, cycle_ctx, start_from)
                except DebugPause:
                    continue
                except Exception as e2:
                    set_phase(db_path, worker, 'failed')
                    set_state_kv(db_path, worker, 'last_error', str(e2)[:400])
                    heartbeat(db_path, worker)
                    return
            if exit_reached:
                set_state_kv(db_path, worker, 'last_error', '')
                set_phase(db_path, worker, 'completed')
                heartbeat(db_path, worker)
                return
            cycle_num += 1
            cycle_id = f"cycle_{cycle_num:03d}"
            continue

        # Normal run (no immediate pause)
        set_phase(db_path, worker, 'running')
        set_state_kv(db_path, worker, 'sleep_until', '')
        set_state_kv(db_path, worker, 'retry_next_at', '')
        heartbeat(db_path, worker)
        try:
            exit_reached = engine.run_cycle(cycle_id, worker_ctx, cycle_ctx, None)
        except DebugPause as e:
            last_step = engine.get_last_step() or {}
            _persist_debug_pause(db_path, worker, cycle_id, last_step, e.next_node or '')
            debug_wait_loop(db_path, worker)
            start_from = get_state_kv(db_path, worker, 'debug.next_node') or e.next_node
            try:
                exit_reached = _resume_after_pause(db_path, worker, engine, cycle_id, worker_ctx, cycle_ctx, start_from)
            except DebugPause:
                continue
            except Exception as e2:
                set_phase(db_path, worker, 'failed')
                set_state_kv(db_path, worker, 'last_error', str(e2)[:400])
                heartbeat(db_path, worker)
                return
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

        # END handled in engine (reloop). We consider a new external cycle here.
        cycle_num += 1
        cycle_id = f"cycle_{cycle_num:03d}"

        if is_canceled(db_path, worker):
            break

    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
