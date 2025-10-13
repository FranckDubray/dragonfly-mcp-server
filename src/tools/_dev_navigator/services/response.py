from typing import Dict, Any


def ensure_envelope(res: Dict[str, Any], operation: str) -> Dict[str, Any]:
    # Ensure standard fields exist and have minimal defaults
    res = dict(res) if isinstance(res, dict) else {"data": res}
    res.setdefault("operation", operation)
    res.setdefault("returned_count", 0)
    res.setdefault("total_count", 0)
    res.setdefault("truncated", False)
    # Keep stats only if explicitly provided by the op (telemetry may add conditionally)
    if "stats" not in res:
        res["stats"] = {}
    # Normalize errors to list if present
    if "errors" in res and not isinstance(res["errors"], list):
        res["errors"] = [res["errors"]]
    # Do not inject next_cursor when absent to keep responses minimal
    return res
