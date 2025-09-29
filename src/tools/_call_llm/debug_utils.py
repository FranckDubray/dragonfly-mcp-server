from typing import Any, Dict
import os


def env_truthy(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in ("1", "true", "yes", "on", "debug")


def trim_str(s: Any, limit: int = 2000) -> Any:
    try:
        if isinstance(s, str) and len(s) > limit:
            return s[:limit] + f"... (+{len(s)-limit} bytes)"
    except Exception:
        pass
    return s


def trim_val(x: Any, limit: int = 2000) -> Any:
    try:
        if isinstance(x, dict):
            return {k: trim_val(v, limit) for k, v in x.items()}
        if isinstance(x, list):
            return [trim_val(v, limit) for v in x]
        if isinstance(x, str):
            return trim_str(x, limit)
    except Exception:
        return x
    return x


def make_debug_container(tool_names: Any) -> Dict[str, Any]:
    return {
        "first": {},
        "tools": {"requested": tool_names or [], "prepared": [], "executions": []},
        "second": {},
        "meta": {},
    }


def attach_stream_debug(target: Dict[str, Any], stream_result: Dict[str, Any], keys=(
    "sse_stats", "raw_preview", "response_headers", "raw", "trace", "provider_preview"
)) -> None:
    for k in keys:
        if k in stream_result:
            target[k] = stream_result.get(k)
