
from typing import Dict, Any, Tuple
from ..runtime import Next, Exit
from ..db import set_phase, set_state_kv, heartbeat, get_state_kv
from ..logging import begin_step, end_step
from ..logging.crash_logger import log_crash
from ..utils.time import utcnow_str
from .sandbox import call_step_sandboxed
from .io_preview import safe_preview, persist_success_inspect
from .usage_accumulator import accumulate_llm_usage


def execute_step(
    db_path: str,
    worker: str,
    process: Any,
    submods: Dict[str, Any],
    current_sub: str,
    current_step: str,
    cycle: Dict[str, Any],
    cycle_id: str,
    env: Any,
) -> Tuple[Any, str]:
    """Execute one step (begin/end logging, sandboxed call). Returns (result, error_message)."""
    sub = submods[current_sub]
    fn = getattr(sub, current_step)
    handler_kind = 'py_cond' if getattr(fn, '_py_orch_cond', False) else 'py_step'
    full_node = f"{current_sub}::{current_step}"
    set_state_kv(db_path, worker, 'debug.phase_trace', f"begin:{full_node}")

    # Snapshot cycle BEFORE (for diff if debug)
    try:
        if get_state_kv(db_path, worker, 'debug.enabled') == 'true':
            set_state_kv(db_path, worker, 'debug.cycle_snapshot_before', safe_preview(cycle))
    except Exception:
        pass

    begin_step(db_path, worker, cycle_id, full_node, handler_kind=handler_kind)
    try:
        res = call_step_sandboxed(fn, process.metadata, cycle, env)
    except Exception as e:
        # Failure path enriched: include last call + preview and also persist into KV
        try:
            call_ctx = env.last_call() if hasattr(env, 'last_call') else {}
        except Exception:
            call_ctx = {}
        try:
            last_res = env.last_result() if hasattr(env, 'last_result') else {}
        except Exception:
            last_res = {}
        # Persist minimal introspection in KV even on failure
        try:
            set_state_kv(db_path, worker, 'py.last_call', safe_preview(call_ctx))
            set_state_kv(db_path, worker, 'py.last_result_preview', safe_preview(last_res))
        except Exception:
            pass
        details = {
            "error": {"message": str(e)[:200]},
            "call": call_ctx,
            "last_result_preview": safe_preview(last_res),
        }
        end_step(db_path, worker, cycle_id, full_node, 'failed', utcnow_str(), details)
        set_state_kv(db_path, worker, 'debug.phase_trace', f"error:{full_node}:{str(e)[:80]}")
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', str(e)[:400])
        try:
            log_crash(db_path, worker, cycle_id=cycle_id, node=full_node, error=e,
                      worker_ctx=process.metadata or {}, cycle_ctx={"call": call_ctx, "last_result": last_res})
        except Exception:
            pass
        heartbeat(db_path, worker)
        return None, str(e)

    # Success path: persist cycle AFTER, compute diff if debug enabled, and persist last_call/preview
    details_success: Dict[str, Any] = {}
    acc_done = False
    try:
        if get_state_kv(db_path, worker, 'debug.enabled') == 'true':
            set_state_kv(db_path, worker, 'debug.cycle_snapshot_after', safe_preview(cycle))
            before = get_state_kv(db_path, worker, 'debug.cycle_snapshot_before') or ''
            after = get_state_kv(db_path, worker, 'debug.cycle_snapshot_after') or ''
            diff = {}
            if before != after:
                diff = {"changed": True, "before": before[:200], "after": after[:200]}
            set_state_kv(db_path, worker, 'debug.ctx_diff', safe_preview(diff))
            # also persist inspect + accumulate LLM usage
            try:
                call = env.last_call() if hasattr(env, 'last_call') else {}
                last_res = env.last_result() if hasattr(env, 'last_result') else {}
                set_state_kv(db_path, worker, 'py.last_call', safe_preview(call))
                set_state_kv(db_path, worker, 'py.last_result_preview', safe_preview(last_res))
                accumulate_llm_usage(db_path, worker, last_res, call)
                acc_done = True
                details_success = {"call": call, "last_result_preview": safe_preview(last_res)}
            except Exception:
                details_success = persist_success_inspect(db_path, worker, env)
    except Exception:
        pass

    # Always persist minimal IO even when debug is off (best-effort)
    try:
        if not acc_done:
            call2 = env.last_call() if hasattr(env, 'last_call') else {}
            last_res2 = env.last_result() if hasattr(env, 'last_result') else {}
            set_state_kv(db_path, worker, 'py.last_call', safe_preview(call2))
            set_state_kv(db_path, worker, 'py.last_result_preview', safe_preview(last_res2))
            # Accumulate LLM usage even when debug is off
            accumulate_llm_usage(db_path, worker, last_res2, call2)
            if isinstance(details_success, dict):
                if 'call' not in details_success:
                    details_success['call'] = call2
                if 'last_result_preview' not in details_success:
                    details_success['last_result_preview'] = safe_preview(last_res2)
    except Exception:
        pass

    # Enrich end_step details
    try:
        d = details_success if isinstance(details_success, dict) else {}
        end_step(db_path, worker, cycle_id, full_node, 'succeeded', utcnow_str(), d)
    except Exception:
        end_step(db_path, worker, cycle_id, full_node, 'succeeded', utcnow_str(), {})

    set_state_kv(db_path, worker, 'debug.phase_trace', f"end:{full_node}")
    return res, ""
