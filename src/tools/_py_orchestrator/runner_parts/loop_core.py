





from typing import Dict, Any, Tuple
import sys
import json as _json
import re
from ..runtime import Next, Exit
from ..db import set_phase, set_state_kv, heartbeat, get_state_kv
from src.tools._orchestrator.logging import begin_step, end_step
from src.tools._orchestrator.logging.crash_logger import log_crash
from src.tools._orchestrator.utils.time import utcnow_str
from .sandbox import call_step_sandboxed


def _safe_preview(obj: Any, max_len: int = 400) -> Any:
    try:
        if isinstance(obj, (dict, list)):
            s = _json.dumps(obj)
            return s if len(s) <= max_len else (s[:max_len] + "…")
        s = str(obj)
        return s if len(s) <= max_len else (s[:max_len] + "…")
    except Exception:
        return str(obj)[:max_len]


# New helper: persist last_call/last_result_preview on success when debug enabled

def _persist_success_inspect(db_path: str, worker: str, env: Any):
    try:
        dbg_enabled = (get_state_kv(db_path, worker, 'debug.enabled') == 'true')
        if not dbg_enabled:
            return {}
        call = env.last_call() if hasattr(env, 'last_call') else {}
        last_res = env.last_result() if hasattr(env, 'last_result') else {}
        details = {"call": call, "last_result_preview": _safe_preview(last_res)}
        # Store compact previews in KV for status consumption
        set_state_kv(db_path, worker, 'py.last_call', _safe_preview(call))
        set_state_kv(db_path, worker, 'py.last_result_preview', _safe_preview(last_res))
        # Also accumulate LLM usage if present
        _accumulate_llm_usage(db_path, worker, last_res)
        return details
    except Exception:
        return {}


# LLM usage accumulation (best-effort)

def _to_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return 0


def _norm_model_key(name: Any) -> str:
    s = str(name or '').strip().lower()
    s = re.sub(r"[^a-z0-9_.\-]+", "_", s)
    return s or "unknown"


def _accumulate_llm_usage(db_path: str, worker: str, last_res: Any):
    try:
        if not isinstance(last_res, dict):
            return
        usage = last_res.get('usage') or last_res.get('token_usage') or {}
        if not isinstance(usage, dict):
            return
        in_tok = _to_int(usage.get('input_tokens') or usage.get('prompt_tokens') or 0)
        out_tok = _to_int(usage.get('output_tokens') or usage.get('completion_tokens') or 0)
        tot_tok = _to_int(usage.get('total_tokens') or (in_tok + out_tok))
        if (in_tok + out_tok + tot_tok) <= 0:
            return
        model = _norm_model_key(last_res.get('model') or usage.get('model') or '')
        # Global counters
        cur_tot = _to_int(get_state_kv(db_path, worker, 'usage.llm.total_tokens') or 0)
        cur_in = _to_int(get_state_kv(db_path, worker, 'usage.llm.input_tokens') or 0)
        cur_out = _to_int(get_state_kv(db_path, worker, 'usage.llm.output_tokens') or 0)
        set_state_kv(db_path, worker, 'usage.llm.total_tokens', str(cur_tot + tot_tok))
        set_state_kv(db_path, worker, 'usage.llm.input_tokens', str(cur_in + in_tok))
        set_state_kv(db_path, worker, 'usage.llm.output_tokens', str(cur_out + out_tok))
        # By model map (JSON in KV)
        import json as _j
        raw = get_state_kv(db_path, worker, 'usage.llm.by_model') or '{}'
        try:
            by_model = _j.loads(raw)
            if not isinstance(by_model, dict):
                by_model = {}
        except Exception:
            by_model = {}
        rec = by_model.get(model) or {}
        rec_tot = _to_int(rec.get('total_tokens') or 0) + tot_tok
        rec_in = _to_int(rec.get('input_tokens') or 0) + in_tok
        rec_out = _to_int(rec.get('output_tokens') or 0) + out_tok
        rec['total_tokens'] = rec_tot
        rec['input_tokens'] = rec_in
        rec['output_tokens'] = rec_out
        by_model[model] = rec
        set_state_kv(db_path, worker, 'usage.llm.by_model', _j.dumps(by_model))
    except Exception:
        pass


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
            set_state_kv(db_path, worker, 'debug.cycle_snapshot_before', _safe_preview(cycle))
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
            set_state_kv(db_path, worker, 'py.last_call', _safe_preview(call_ctx))
            set_state_kv(db_path, worker, 'py.last_result_preview', _safe_preview(last_res))
        except Exception:
            pass
        details = {
            "error": {"message": str(e)[:200]},
            "call": call_ctx,
            "last_result_preview": _safe_preview(last_res),
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
    try:
        if get_state_kv(db_path, worker, 'debug.enabled') == 'true':
            set_state_kv(db_path, worker, 'debug.cycle_snapshot_after', _safe_preview(cycle))
            # naive diff (string-level best effort for preview)
            before = get_state_kv(db_path, worker, 'debug.cycle_snapshot_before') or ''
            after = get_state_kv(db_path, worker, 'debug.cycle_snapshot_after') or ''
            diff = {}
            if before != after:
                diff = {"changed": True, "before": before[:200], "after": after[:200]}
            set_state_kv(db_path, worker, 'debug.ctx_diff', _safe_preview(diff))
            details_success = _persist_success_inspect(db_path, worker, env)
    except Exception:
        pass

    # Enrich end_step details on success when debug.enabled (for recent_steps timeline)
    try:
        d = details_success if isinstance(details_success, dict) else {}
        end_step(db_path, worker, cycle_id, full_node, 'succeeded', utcnow_str(), d)
    except Exception:
        end_step(db_path, worker, cycle_id, full_node, 'succeeded', utcnow_str(), {})

    set_state_kv(db_path, worker, 'debug.phase_trace', f"end:{full_node}")
    return res, ""
