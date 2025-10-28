
from __future__ import annotations
from typing import Any, Dict
import json as _json
from ..db import set_state_kv, get_state_kv

__all__ = [
    "safe_preview",
    "persist_success_inspect",
]


def safe_preview(obj: Any, max_len: int = 400) -> Any:
    try:
        if isinstance(obj, (dict, list)):
            s = _json.dumps(obj)
            return s if len(s) <= max_len else (s[:max_len] + "…")
        s = str(obj)
        return s if len(s) <= max_len else (s[:max_len] + "…")
    except Exception:
        return str(obj)[:max_len]


def persist_success_inspect(db_path: str, worker: str, env: Any) -> Dict[str, Any]:
    """When debug is enabled, persist last_call and last_result preview to KV and return details dict."""
    try:
        dbg_enabled = (get_state_kv(db_path, worker, 'debug.enabled') == 'true')
        if not dbg_enabled:
            return {}
        call = env.last_call() if hasattr(env, 'last_call') else {}
        last_res = env.last_result() if hasattr(env, 'last_result') else {}
        details = {"call": call, "last_result_preview": safe_preview(last_res)}
        set_state_kv(db_path, worker, 'py.last_call', safe_preview(call))
        set_state_kv(db_path, worker, 'py.last_result_preview', safe_preview(last_res))
        return details
    except Exception:
        return {}
