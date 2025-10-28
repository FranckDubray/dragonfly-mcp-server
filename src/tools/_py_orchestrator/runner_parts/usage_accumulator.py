
from __future__ import annotations
from typing import Any, Dict
import re
from ..db import get_state_kv, set_state_kv

__all__ = [
    "accumulate_llm_usage",
]


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            try:
                import re as _re
                m = _re.search(r"[-+]?\d+", str(v))
                return int(m.group(0)) if m else 0
            except Exception:
                return 0


def _norm_model_key(name: Any) -> str:
    s = str(name or '').strip().lower()
    s = re.sub(r"[^a-z0-9_.\-]+", "_", s)
    return s or "unknown"


def accumulate_llm_usage(db_path: str, worker: str, last_res: Any, call_ctx: Dict[str, Any] | None = None) -> None:
    """Best-effort LLM usage accumulation into KV.
    Accepts usage/ token_usage under result or top-level; supports multiple field namings.
    Updates:
      - usage.llm.total_tokens / input_tokens / output_tokens
      - usage.llm.by_model.{model}
    """
    try:
        if not isinstance(last_res, dict):
            return
        # Sometimes usage/model live under an inner 'result'
        src = last_res
        if 'usage' not in src and isinstance(last_res.get('result'), dict):
            src = last_res.get('result') or {}

        usage = src.get('usage') or src.get('token_usage') or {}
        if not isinstance(usage, dict):
            return

        in_tok = _to_int(
            usage.get('input_tokens')
            or usage.get('prompt_tokens')
            or usage.get('prompt')
            or usage.get('input')
            or usage.get('tokens_in')
            or 0
        )
        out_tok = _to_int(
            usage.get('output_tokens')
            or usage.get('completion_tokens')
            or usage.get('completion')
            or usage.get('output')
            or usage.get('tokens_out')
            or 0
        )
        tot_tok = _to_int(
            usage.get('total_tokens')
            or usage.get('total')
            or usage.get('tokens')
            or 0
        )
        if tot_tok <= 0:
            tot_tok = in_tok + out_tok
        if (in_tok + out_tok + tot_tok) <= 0:
            return

        # Prefer explicit model fields; fallback to call params
        model = src.get('model') or usage.get('model')
        if not model and isinstance(call_ctx, dict):
            params = call_ctx.get('params') or {}
            model = params.get('model')
        model = _norm_model_key(model)

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
        # Best effort only
        pass
