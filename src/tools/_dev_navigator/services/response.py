from typing import Dict, Any


def ensure_envelope(res: Dict[str, Any], operation: str) -> Dict[str, Any]:
    # Ensure standard fields exist and have minimal defaults
    res = dict(res) if isinstance(res, dict) else {"data": res}
    res.setdefault("operation", operation)
    res.setdefault("returned_count", 0)
    res.setdefault("total_count", 0)
    res.setdefault("truncated", False)
    res.setdefault("stats", {})
    # Optional standard fields
    if "errors" in res and not isinstance(res["errors"], list):
        res["errors"] = [res["errors"]]
    if "next_cursor" not in res:
        res["next_cursor"] = None
    # fs_requests optional: keep if provided
    return res
