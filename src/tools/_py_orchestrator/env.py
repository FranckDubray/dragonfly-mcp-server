













from typing import Any, Dict
from .handlers import bootstrap_handlers as bootstrap_local, get_registry as get_registry_local
from .http_tool import HttpToolHandler

_SENSITIVE_KEYS = {"api_key","apikey","authorization","auth","token","access_token","secret","password"}

def _sanitize(obj: Any, max_len: int = 400) -> Any:
    """Sanitize params/results for logging: mask secrets, truncate long strings, shallow copy."""
    try:
        if isinstance(obj, dict):
            out: Dict[str, Any] = {}
            for k, v in obj.items():
                lk = str(k).lower()
                if lk in _SENSITIVE_KEYS:
                    out[k] = "****"
                elif isinstance(v, str):
                    out[k] = v if len(v) <= max_len else (v[:max_len] + "…")
                else:
                    out[k] = v
            return out
        if isinstance(obj, str):
            return obj if len(obj) <= max_len else (obj[:max_len] + "…")
        return obj
    except Exception:
        return obj

class PyEnv:
    def __init__(self, cancel_flag_fn, worker_ctx: Dict[str, Any] | None = None):
        # Bootstrap local, built-in transforms (tool autonomy)
        bootstrap_local(cancel_flag_fn)
        self._registry = get_registry_local()  # registry object with .get(kind)
        # Configure HTTP tool handler timeout from worker context (fallback 30s)
        http_timeout = 30.0
        try:
            if isinstance(worker_ctx, dict):
                http_timeout = float(worker_ctx.get('http_timeout_sec', http_timeout))
        except Exception:
            pass
        # Autonomous HTTP tool handler to call MCP tools
        self._http = HttpToolHandler(timeout=http_timeout)
        self._last_result: Dict[str, Any] = {}
        self._last_call: Dict[str, Any] = {}

    def tool(self, tool: str, **kwargs) -> Dict[str, Any]:
        # record last call context (sanitized)
        call_params = dict(kwargs)
        self._last_call = {"kind": "tool", "name": tool, "params": _sanitize(call_params)}
        payload = {**kwargs, 'tool': tool}
        res = self._http.run(**payload)
        # Unwrap common MCP envelope {"result": ...} when no error/status fields are present
        # but PRESERVE sibling metadata (e.g., model, usage) instead of dropping them.
        try:
            if isinstance(res, dict) and ('result' in res) and not any(k in res for k in ('accepted','status','error','message','details')):
                inner = res.get('result')
                # Merge dict-like result with top-level siblings (except 'result')
                if isinstance(inner, dict):
                    base = {k: v for k, v in res.items() if k != 'result'}
                    res = {**inner, **base}
                else:
                    # Keep scalar result as 'content' while preserving siblings
                    res = {**res, 'content': inner}
                    res.pop('result', None)
        except Exception:
            pass
        # Persist last result (best effort, sanitized preview)
        self._last_result = res if isinstance(res, dict) else {'content': res}
        # Auto-fail fast if MCP returned an error envelope so the runner logs it
        try:
            if isinstance(res, dict):
                status = str(res.get('status') or '').lower()
                accepted = res.get('accepted')
                # Also catch tools that return an 'error' field instead of accepted/status
                raw_error = res.get('error')
                if raw_error:
                    msg = str(res.get('message') or raw_error)
                    details = res.get('details')
                    d = ''
                    if isinstance(details, (str, bytes)):
                        d = (details.decode('utf-8', 'ignore') if isinstance(details, bytes) else details)[:400]
                    elif isinstance(details, dict):
                        try:
                            import json as _json
                            d = _json.dumps(_sanitize(details))[:400]
                        except Exception:
                            d = str(details)[:400]
                    raise RuntimeError(f"TOOL({tool}) error: {msg} | details: {d}")
                if accepted is False or status in {'error', 'failed'}:
                    msg = str(res.get('message') or 'Tool error')
                    details = res.get('details')
                    d = ''
                    if isinstance(details, (str, bytes)):
                        d = (details.decode('utf-8', 'ignore') if isinstance(details, bytes) else details)[:400]
                    elif isinstance(details, dict):
                        try:
                            import json as _json
                            d = _json.dumps(_sanitize(details))[:400]
                        except Exception:
                            d = str(details)[:400]
                    raise RuntimeError(f"TOOL({tool}) error: {msg} | details: {d}")
        except Exception:
            # Re-raise to be caught by runner and properly logged as failed step
            raise
        return res

    def transform(self, kind: str, **kwargs) -> Dict[str, Any]:
        # record last call context (sanitized)
        self._last_call = {"kind": "transform", "name": kind, "params": _sanitize(dict(kwargs))}
        h = self._registry.get(kind)
        res = h.run(**kwargs)
        self._last_result = res if isinstance(res, dict) else {'result': res}
        return res

    def last_result(self) -> Dict[str, Any]:
        return self._last_result or {}

    def last_call(self) -> Dict[str, Any]:
        return self._last_call or {}

 
 
 
 
 
 
 
 
