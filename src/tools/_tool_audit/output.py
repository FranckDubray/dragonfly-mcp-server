from __future__ import annotations
from typing import Any, Dict


def build_response(tool_name: str, fused: Dict[str, Any], limit: int, cursor: str | None, fields: str) -> Dict[str, Any]:
    findings = fused.get("findings", [])
    total = len(findings)
    page = findings[:limit]
    truncated = total > limit

    out = {
        "tool_name": tool_name,
        "summary": {
            **fused.get("summary", {}),
            "total_findings": total,
            "returned_count": len(page),
            "truncated": truncated,
        },
        "scores": fused.get("scores", {}),
        "git_sensitive": fused.get("git_sensitive", {}),
        "findings": page,
        "actions": fused.get("actions", {}),
        "fs_requests": fused.get("fs_requests", []),
    }

    if truncated:
        out["message"] = "Results truncated to limit; use cursor for next page"
    return out
