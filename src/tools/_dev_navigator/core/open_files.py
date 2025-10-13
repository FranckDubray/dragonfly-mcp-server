from typing import Any, Dict, List


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    # FS-first: we do not return file contents, only a plan for the client FS tool
    paths: List[str] = p.get("paths") or p.get("pins") or []
    if not isinstance(paths, list):
        return {
            "operation": "open",
            "errors": [{"code": "invalid_parameters", "message": "paths must be an array of strings", "scope": "tool", "recoverable": True}],
            "returned_count": 0, "total_count": 0, "truncated": False
        }
    # Head ranges proposal (client can adjust): first 80 lines for up to 5 files
    max_files = min(len(paths), max(1, min(p.get("limit", 20), 5)))
    plan = [{"path": paths[i], "ranges": [{"start_line": 1, "end_line": 80}]} for i in range(max_files)]
    return {
        "operation": "open",
        "data": [],
        "fs_requests": plan,
        "returned_count": 0,
        "total_count": len(paths),
        "truncated": len(paths) > max_files,
        "next_cursor": None,
        "stats": {"requested_files": len(paths), "planned_files": max_files}
    }
