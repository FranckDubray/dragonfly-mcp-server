

from typing import Dict, Any
from ..db import get_state_kv, set_state_kv, set_phase, heartbeat
from src.tools._orchestrator.debug_loop import debug_wait_loop


def persist_debug_pause(db_path: str, worker: str, step_name: str, next_name: str, cycle_id: str):
    set_phase(db_path, worker, 'debug_paused')
    set_state_kv(db_path, worker, 'debug.cycle_id', cycle_id)
    set_state_kv(db_path, worker, 'debug.paused_at', step_name or '')
    set_state_kv(db_path, worker, 'debug.next_node', next_name or '')
    set_state_kv(db_path, worker, 'debug.last_step', '{"node":"%s","type":"py_step"}' % (step_name or ''))
    req_id = get_state_kv(db_path, worker, 'debug.req_id') or ''
    set_state_kv(db_path, worker, 'debug.response_id', req_id)
    heartbeat(db_path, worker)


def maybe_pause_on_breakpoint(db_path: str, worker: str, current_sub: str, current_step: str, cycle_id: str):
    from src.tools._orchestrator.runner_helpers import get_debug_state
    dbg = get_debug_state(db_path, worker) or {}
    bps = dbg.get('breakpoints') or []
    if bps and any(bp.get('node') in {current_step, f"{current_sub}::{current_step}"} for bp in bps):
        persist_debug_pause(db_path, worker, step_name=f"{current_sub}::{current_step}", next_name=f"{current_sub}::{current_step}", cycle_id=cycle_id)
        debug_wait_loop(db_path, worker)


def maybe_pause_on_step_mode(db_path: str, worker: str, full_node: str, next_node: str, cycle_id: str):
    from src.tools._orchestrator.runner_helpers import is_debug_enabled, get_debug_state
    if not is_debug_enabled(db_path, worker):
        return
    dbg = get_debug_state(db_path, worker) or {}
    if dbg.get('mode') == 'step' or dbg.get('mode') is None:
        persist_debug_pause(db_path, worker, step_name=full_node, next_name=next_node, cycle_id=cycle_id)
        debug_wait_loop(db_path, worker)


def maybe_pause_on_until(db_path: str, worker: str, current_sub: str, current_step: str, cycle_id: str):
    """Pause right before executing the target node if debug.until matches the upcoming full node.
    Clears debug.until and waits in debug loop.
    """
    try:
        target = get_state_kv(db_path, worker, 'debug.until') or ''
        if not target:
            return
        full_node = f"{current_sub}::{current_step}"
        if target == full_node:
            # clear until and pause
            set_state_kv(db_path, worker, 'debug.until', '')
            persist_debug_pause(db_path, worker, step_name=full_node, next_name=full_node, cycle_id=cycle_id)
            debug_wait_loop(db_path, worker)
    except Exception:
        return
