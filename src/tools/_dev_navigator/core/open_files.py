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


def _clamp_head_lines(n: int) -> int:
    try:
        n = int(n)
    except Exception:
        return 80
    if n < 10:
        return 10
    if n > 200:
        return 200
    return n


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    # FS-first: we do not return file contents, only a plan for the client FS tool
    # Guard against misuses requesting "full" fields
    if p.get("fields") == "full":
        return {
            "operation": "open",
            "errors": [{
                "code": "invalid_parameters",
                "message": "open returns a plan only (fs_requests). No file contents are returned.",
                "scope": "tool",
                "recoverable": True
            }],
            "returned_count": 0, "total_count": 0, "truncated": False
        }

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

    # Batch planning: up to 'limit' files (hard-cap 50 to keep plan compact)
    req_limit = p.get("limit", 20)
    try:
        req_limit = int(req_limit)
    except Exception:
        req_limit = 20
    if req_limit < 1:
        req_limit = 1
    if req_limit > 50:
        req_limit = 50

    head_lines = _clamp_head_lines(p.get("head_lines", 80))

    max_files = min(len(paths), req_limit)
    plan = [{"path": paths[i], "ranges": [{"start_line": 1, "end_line": head_lines}]} for i in range(max_files)]
    return {
        "operation": "open",
        "data": [],
        "fs_requests": plan,
        "notice": "This operation returns a plan (fs_requests) only. Use your FS tool to read file contents.",
        "returned_count": 0,
        "total_count": len(paths),
        "truncated": len(paths) > max_files,
        "next_cursor": None,
        "stats": {"requested_files": len(paths), "planned_files": max_files, "head_lines": head_lines}
    }
