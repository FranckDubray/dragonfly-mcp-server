from __future__ import annotations
from typing import Any, Dict, Optional


def merge_usage(into: Dict[str, Any], add: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not add or not isinstance(add, dict):
        return into
    for k, v in add.items():
        try:
            if isinstance(v, (int, float)) and ("price" not in k.lower()):
                if isinstance(into.get(k), (int, float)):
                    into[k] += v
                elif k not in into:
                    into[k] = v
            else:
                if k not in into:
                    into[k] = v
        except Exception:
            if k not in into:
                into[k] = v
    return into
