from typing import Any, Dict, List
import os

from ..services.errors import make_error
from ..services.fs_scanner import DEFAULT_EXCLUDE_FILES_PREFIX


def _is_blocked_doc(path: str) -> bool:
    up = os.path.basename(path).upper()
    if any(up.startswith(pref) for pref in DEFAULT_EXCLUDE_FILES_PREFIX):
        return True
    # common docs folders
    norm = path.replace("\\", "/").lower()
    if norm.startswith("docs/") or norm.startswith("changelogs/"):
        return True
    return False


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    # FS-first: we do not return file contents, only a plan for the client FS tool
    paths: List[str] = p.get("paths") or p.get("pins") or []
    if not isinstance(paths, list):
        return {
            "operation": "open",
            "errors": [{"code": "invalid_parameters", "message": "paths must be an array of strings", "scope": "tool", "recoverable": True}],
            "returned_count": 0, "total_count": 0, "truncated": False
        }

    # Doc policy enforcement for README/CHANGELOG/docs/* by default
    policy = p.get("doc_policy", "outline_only")
    allowlist = set(p.get("explicit_allowlist") or [])
    blocked: List[str] = []
    for path in paths:
        if _is_blocked_doc(path):
            if policy != "allow_docs" or path not in allowlist:
                blocked.append(path)
    if blocked:
        return {
            "operation": "open",
            "errors": [{
                "code": "doc_policy_blocked",
                "message": f"Blocked by doc_policy={policy}; explicit_allowlist required for: {blocked[:3]}" + ("…" if len(blocked) > 3 else ""),
                "scope": "file",
                "recoverable": True
            }],
            "returned_count": 0, "total_count": len(paths), "truncated": False
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
