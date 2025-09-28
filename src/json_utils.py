"""
JSON utilities for handling special float values (inf, -inf, nan)
"""
import json
import math
from typing import Any, Dict


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object to make it JSON-compliant.
    Converts inf/-inf/nan values to strings.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        elif math.isnan(obj):
            return "NaN"
        else:
            return obj
    else:
        return obj


def safe_json_response(content: Any) -> Dict[str, Any]:
    """
    Create a JSON-safe response by sanitizing the content.
    """
    return {"result": sanitize_for_json(content)}


def json_compliant_dumps(obj: Any, **kwargs) -> str:
    """
    JSON dumps that handles special float values.
    """
    sanitized = sanitize_for_json(obj)
    return json.dumps(sanitized, **kwargs)