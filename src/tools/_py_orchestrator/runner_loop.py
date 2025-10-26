from typing import Dict, Any
import time

from .db import get_state_kv, set_state_kv, set_phase, heartbeat
from .runtime import Next, Exit
from .env import PyEnv
from .hash_utils import compute_dir_uid
from src.tools._orchestrator.runner_helpers import is_canceled
from .runner_parts.loader import load_worker_root, load_module
from .runner_parts.debugging import (
    persist_debug_pause,
    maybe_pause_on_breakpoint,
    maybe_pause_on_step_mode,
    maybe_pause_on_until,
)
from .runner_parts.summary import persist_summary_if_any
from .runner_parts.preflight import preflight_load_graph, set_graph_metadata
from .runner_parts.reloader import maybe_hot_reload
from src.tools._orchestrator.logging.crash_logger import log_crash
from src.tools._orchestrator.debug_loop import debug_wait_loop
from .runner_parts.loop_core import execute_step


def run_loop(db_path: str, worker: str):
    root = load_worker_root(worker)

    graph, err = preflight_load_graph(root, db_path, worker)
    if graph is None:
        return
    set_graph_metadata(db_path, worker, graph)

    uid = compute_dir_uid(root)
    set_state_kv(db_path, worker, 'process_uid', uid)

    try:
        proc_mod = load_module(f"pyworker_{worker}_process", root / 'process.py')
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'Load process failed: {str(e)[:300]}')
        try:
            log_crash(db_path, worker, cycle_id='startup', node='process_import', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        return
    process = proc_mod.PROCESS

    submods: Dict[str, Any] = {}
    try:
        for ref in process.parts:
            mod = load_module(
                f"pyworker_{worker}_{ref.name}",
                root / (ref.module.replace('.', '/') + '.py'),
            )
            submods[ref.name] = mod
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'Import subgraph failed: {str(e)[:300]}')
        try:
            log_crash(db_path, worker, cycle_id='startup', node='subgraph_import', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        return

    order = graph.get('order') or []
    subgraph_infos: Dict[str, Any] = graph.get('subgraphs', {})
    current_sub = process.entry
    current_step = submods[current_sub].SUBGRAPH.entry

    cycle: Dict[str, Any] = {}
    env = PyEnv(lambda: is_canceled(db_path, worker))

    cycle_num = 1
    cycle_id = f"cycle_{cycle_num:03d}"

    # Pause immédiate: exposer next_node et bloquer réellement
    if (get_state_kv(db_path, worker, 'debug.pause_request') or '') == 'immediate':
        set_state_kv(db_path, worker, 'debug.pause_request', '')
        next_full = f"{current_sub}::{current_step}"
        set_state_kv(db_path, worker, 'debug.next_node', next_full)
        set_state_kv(db_path, worker, 'debug.phase_trace', f'pause_init_set:{next_full}')
        set_state_kv(db_path, worker, 'debug.paused_at', next_full)
        time.sleep(0.03)
        persist_debug_pause(db_path, worker, step_name='', next_name=next_full, cycle_id=cycle_id)
        debug_wait_loop(db_path, worker)

    while not is_canceled(db_path, worker):
        if (get_state_kv(db_path, worker, 'hot_reload') == 'true'):
            (
                uid,
                new_graph,
                new_process,
                new_submods,
                new_order,
                new_subgraph_infos,
                new_current_sub,
                new_current_step,
            ) = maybe_hot_reload(root, db_path, worker, uid)
            if new_graph is not None:
                graph = new_graph
                process = new_process
                submods = new_submods
                order = new_order
                subgraph_infos = new_subgraph_infos
                current_sub = new_current_sub
                current_step = new_current_step

        set_phase(db_path, worker, 'running')
        heartbeat(db_path, worker)

        # Pause on until target / breakpoints (before executing the node)
        maybe_pause_on_until(db_path, worker, current_sub, current_step, cycle_id)
        maybe_pause_on_breakpoint(db_path, worker, current_sub, current_step, cycle_id)

        full_node = f"{current_sub}::{current_step}"
        set_state_kv(db_path, worker, 'debug.executing_node', full_node)
        res, err = execute_step(
            db_path=db_path,
            worker=worker,
            process=process,
            submods=submods,
            current_sub=current_sub,
            current_step=current_step,
            cycle=cycle,
            cycle_id=cycle_id,
            env=env,
        )
        set_state_kv(db_path, worker, 'debug.executing_node', '')
        if err:
            heartbeat(db_path, worker)
            return

        if isinstance(res, Next):
            next_step = res.target
            maybe_pause_on_step_mode(db_path, worker, full_node, f"{current_sub}::{next_step}", cycle_id)
            current_step = next_step
            continue

        if isinstance(res, Exit):
            exit_name = res.name or 'success'
            info = subgraph_infos.get(current_sub, {})
            nxt = (info.get('next') or {})
            target_sg = nxt.get(exit_name)
            if target_sg and target_sg in submods:
                current_sub = target_sg
                current_step = submods[current_sub].SUBGRAPH.entry
                maybe_pause_on_step_mode(db_path, worker, full_node, f"{current_sub}::{current_step}", cycle_id)
                continue
            try:
                idx = order.index(current_sub)
            except ValueError:
                idx = -1
            if exit_name == 'success' and idx != -1 and idx < len(order) - 1:
                current_sub = order[idx + 1]
                current_step = submods[current_sub].SUBGRAPH.entry
                maybe_pause_on_step_mode(db_path, worker, full_node, f"{current_sub}::{current_step}", cycle_id)
                continue
            persist_summary_if_any(db_path, worker, cycle)
            set_phase(db_path, worker, 'completed')
            heartbeat(db_path, worker)
            return

        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'Invalid step return from {full_node}')
        heartbeat(db_path, worker)
        return

    set_phase(db_path, worker, 'canceled')
    heartbeat(db_path, worker)
