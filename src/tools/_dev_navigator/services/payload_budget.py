import json
from typing import Dict, Any

from .constants import MAX_PAYLOAD_BYTES


def measure_bytes(obj: Dict[str, Any]) -> int:
    # Safe JSON measurement (approx by dumps utf-8 length)
    try:
        s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return len(s.encode("utf-8"))
    except Exception:
        # fallback rough estimate
        return 10_000_000


def enforce_cap(response: Dict[str, Any]) -> Dict[str, Any]:
    # If payload exceeds MAX_PAYLOAD_BYTES, try to shrink predictable fields
    size = measure_bytes(response)
    if size <= MAX_PAYLOAD_BYTES:
        return response

    # Progressive reductions
    # 1) Remove snippets fields if present
    def strip_snippets(node):
        if isinstance(node, dict):
            for k in list(node.keys()):
                if k in ("snippet", "snippets"):
                    node.pop(k, None)
                else:
                    strip_snippets(node[k])
        elif isinstance(node, list):
            for it in node:
                strip_snippets(it)

    strip_snippets(response)
    size = measure_bytes(response)
    response["truncated"] = True
    if size <= MAX_PAYLOAD_BYTES:
        return response

    # 2) Trim data arrays in common sections
    def trim_array(key):
        if key in response and isinstance(response[key], list):
            response[key] = response[key][:1]  # keep minimal

    for key in ("data", "fs_requests"):
        trim_array(key)
    size = measure_bytes(response)
    if size <= MAX_PAYLOAD_BYTES:
        return response

    # 3) If still too large, return minimal error envelope
    return {
        "operation": response.get("operation", "unknown"),
        "errors": [{"code": "budget_exceeded", "message": "payload > 20KB", "scope": "tool", "recoverable": True}],
        "returned_count": 0,
        "total_count": 0,
        "truncated": True,
        "stats": response.get("stats", {})
    }
