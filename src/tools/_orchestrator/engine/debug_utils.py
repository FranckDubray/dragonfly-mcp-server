from typing import Any, Dict, Optional
import json
import re
from datetime import datetime, timezone

MAX_PREVIEW_BYTES = 100  # ~0.1 KB per value
MAX_ARRAY_ITEMS = 50

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_KEYS = {"password", "token", "api_key", "apikey", "secret", "access_token", "refresh_token"}

class DebugPause(Exception):
    """Signifies a debug pause request after executing a node."""
    def __init__(self, next_node: Optional[str]):
        super().__init__("Debug pause")
        self.next_node = next_node

# -- Small time helper (no engine dependency) --

def utcnow_str() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

# -- redaction helpers --

def _mask_pii(s: str) -> str:
    try:
        return EMAIL_RE.sub("***@***.***", s)
    except Exception:
        return s

def _redact_dict_shallow(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        lk = str(k).lower()
        if any(sk in lk for sk in SECRET_KEYS):
            out[k] = "REDACTED"
        else:
            out[k] = v
    return out

# -- ctx diff + redaction/truncation utilities --

def _preview(value: Any) -> Any:
    try:
        # Redact shallow secrets in dicts first
        if isinstance(value, dict):
            value = _redact_dict_shallow(value)
        # Truncate long arrays
        if isinstance(value, list) and len(value) > MAX_ARRAY_ITEMS:
            head = value[:MAX_ARRAY_ITEMS]
            return {
                "preview": [_preview(item) for item in head],
                "truncated": True,
                "total_count": len(value)
            }
        # Serialize to JSON string for byte-precise truncation
        s = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        s = str(value)
    try:
        s_masked = _mask_pii(s)
    except Exception:
        s_masked = s
    b = s_masked.encode('utf-8')
    if len(b) > MAX_PREVIEW_BYTES:
        head = b[:MAX_PREVIEW_BYTES].decode('utf-8', errors='ignore')
        return f"{head}... (truncated, total: {len(b)} bytes)"
    return s_masked if isinstance(value, (dict, list)) else s_masked

def compute_ctx_diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    added: Dict[str, Any] = {}
    changed: Dict[str, Any] = {}
    deleted = []
    before_keys = set(before.keys())
    after_keys = set(after.keys())
    for k in sorted(after_keys - before_keys):
        added[f"cycle.{k}"] = _preview(after[k])
    for k in sorted(before_keys - after_keys):
        deleted.append(f"cycle.{k}")
    for k in sorted(before_keys & after_keys):
        if before[k] != after[k]:
            changed[f"cycle.{k}"] = {"old": _preview(before[k]), "new": _preview(after[k])}
    return {"added": added, "changed": changed, "deleted": deleted}

# -- step summary --

def mk_step_summary(details: Dict[str, Any], started_at: str) -> Dict[str, Any]:
    try:
        start_dt = datetime.fromisoformat(started_at.replace(' ', 'T'))
        end_dt = datetime.fromisoformat(utcnow_str().replace(' ', 'T'))
        duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
    except Exception:
        duration_ms = None
    summary = {
        "node": details.get('node'),
        "type": details.get('type'),
        "handler_kind": details.get('handler_kind'),
        "duration_ms": duration_ms,
    }
    if 'edge_taken' in details:
        summary['edge_taken'] = details['edge_taken']
    if 'attempts' in details:
        summary['attempts'] = details['attempts']
    return summary

# -- pause policy --

def should_pause_after(debug_state: Dict[str, Any] | None, node: Dict[str, Any], route: str) -> bool:
    if not debug_state or not debug_state.get('enabled'):
        return False
    mode = debug_state.get('mode', 'step')
    if mode == 'step':
        return True
    if mode == 'continue':
        bps = debug_state.get('breakpoints') or []
        for bp in bps:
            if bp.get('node') == node.get('name'):
                when = bp.get('when')
                if when is None or when == route:
                    return True
    if mode == 'until':
        target = debug_state.get('until') or {}
        if target.get('node') == node.get('name'):
            when = target.get('when')
            if when is None or when == route:
                return True
    return False
