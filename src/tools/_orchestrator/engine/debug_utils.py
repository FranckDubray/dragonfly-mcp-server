












from typing import Any, Dict, Optional
import json
import re
from datetime import datetime, timezone

# Import centralized time utility
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import utcnow_str

MAX_PREVIEW_BYTES = 10_000  # 10 KB as requested
MAX_ARRAY_ITEMS = 50

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_KEYS = {"password", "token", "api_key", "apikey", "secret", "access_token", "refresh_token"}

class DebugPause(Exception):
    def __init__(self, next_node: Optional[str]):
        super().__init__("Debug pause")
        self.next_node = next_node

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

# previews

def _preview(value: Any) -> Any:
    try:
        if isinstance(value, dict):
            value = _redact_dict_shallow(value)
        if isinstance(value, list) and len(value) > MAX_ARRAY_ITEMS:
            head = value[:MAX_ARRAY_ITEMS]
            return {
                "preview": [_preview(item) for item in head],
                "truncated": True,
                "total_count": len(value)
            }
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

# ctx diff

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

# step summary WITH DEBUG ENRICHMENT

def mk_step_summary(details: Dict[str, Any], started_at: str, 
                   inputs: Dict[str, Any] = None, 
                   outputs: Dict[str, Any] = None,
                   cycle_ctx: Dict[str, Any] = None) -> Dict[str, Any]:
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
    
    # Attach debug previews if present in details
    if 'debug_preview' in details:
        summary['debug_preview'] = details['debug_preview']
    
    # ENRICHMENT: Add inputs/outputs/ctx_keys for better debugging
    debug_info = {}
    
    if inputs is not None:
        try:
            debug_info['inputs_preview'] = _preview(inputs)
        except Exception:
            pass
    
    if outputs is not None:
        try:
            debug_info['outputs_preview'] = _preview(outputs)
        except Exception:
            pass
    
    if cycle_ctx is not None:
        try:
            debug_info['ctx_keys'] = list(cycle_ctx.keys())
            # Count total keys recursively
            total_keys = 0
            for scope_name, scope_data in cycle_ctx.items():
                if isinstance(scope_data, dict):
                    total_keys += len(scope_data)
            debug_info['ctx_total_keys'] = total_keys
        except Exception:
            pass
    
    if debug_info:
        summary['debug_info'] = debug_info
    
    return summary

# pause policy

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

# truncation detection (shared)

def is_truncated_preview(obj: Any, max_bytes: int = MAX_PREVIEW_BYTES) -> bool:
    """
    Returns True if the preview payload is considered truncated, based on:
      - total serialized size exceeding max_bytes, or
      - presence of inner truncation markers produced by _preview (truncated=True or "(truncated, total:")
    """
    try:
        def _has_trunc(o: Any) -> bool:
            if isinstance(o, dict):
                if o.get('truncated') is True:
                    return True
                for v in o.values():
                    if _has_trunc(v):
                        return True
                return False
            if isinstance(o, list):
                for v in o:
                    if _has_trunc(v):
                        return True
                return False
            if isinstance(o, str) and '(truncated, total:' in o:
                return True
            return False
        s = json.dumps(obj, ensure_ascii=False)
        if len(s) > max_bytes:
            return True
        return _has_trunc(obj)
    except Exception:
        return False

# sanitize details for logs (PII masking + truncation + size cap)

def sanitize_details_for_log(details: Dict[str, Any], max_bytes: int = MAX_PREVIEW_BYTES) -> Dict[str, Any]:
    """
    Return a sanitized copy of details suitable for persistent logs.
    - masks secrets by key name
    - truncates long strings (>200 chars)
    - limits arrays to 50 items with preview metadata
    - sets details['truncated']=True if resulting JSON exceeds max_bytes (and drops bulky debug_preview)
    """
    import copy
    def _sanitize(obj: Any) -> Any:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                lk = str(k).lower()
                if any(sk in lk for sk in SECRET_KEYS):
                    out[k] = "REDACTED"
                    continue
                out[k] = _sanitize(v)
            return out
        if isinstance(obj, list):
            if len(obj) > MAX_ARRAY_ITEMS:
                head = [_sanitize(x) for x in obj[:MAX_ARRAY_ITEMS]]
                return {"preview": head, "truncated": True, "total_count": len(obj)}
            return [_sanitize(x) for x in obj]
        if isinstance(obj, str):
            s = _mask_pii(obj)
            if len(s) > 200:
                return f"{s[:200]}... (truncated, total: {len(s)} chars)"
            return s
        return obj

    clean = _sanitize(copy.deepcopy(details or {}))
    try:
        s = json.dumps(clean, ensure_ascii=False, separators=(',', ':'))
        if len(s) > max_bytes:
            # Drop heavy debug_preview if present, mark truncated
            if isinstance(clean, dict) and 'debug_preview' in clean:
                clean['debug_preview'] = "omitted due to size"
            clean['truncated'] = True
        return clean
    except Exception:
        return {"error": "failed to sanitize details"}

 
 
 
 
 
 
 
 
 
 
 
