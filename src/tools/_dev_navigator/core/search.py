from typing import Any, Dict, List
import os

from ..services.pagination import paginate_list
from ..services.pathing import resolve_root_and_abs
from ..services.fs_scanner import iter_files
from ..services.globber import allowed_by_globs
from ..services.budget_broker import compute_effective_budgets
from ..services.constants import DEFAULT_MAX_HITS_PER_FILE
from ..services.anchors import make_anchor
from ..connectors.python.search_regex import search_in_file


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    pattern = p.get("query")
    if not pattern:
        return {
            "operation": "search",
            "errors": [{"code": "invalid_parameters", "message": "query is required", "scope": "tool", "recoverable": True}],
            "returned_count": 0, "total_count": 0, "truncated": False
        }
    case_sensitive = bool(p.get("case_sensitive", False))
    includes = p.get("glob_include") or []
    excludes = p.get("glob_exclude") or []

    eff = compute_effective_budgets(p)
    limit = eff["limit"]
    mhpf = eff["max_hits_per_file"]

    root = p["path"]
    scope_path = p.get("scope_path")

    # Collect raw hits (anchors-only, FS-first)
    hits: List[Dict[str, Any]] = []
    scanned = 0
    for rel, _size in iter_files(root, scope_path, eff["max_files_scanned"]):
        if not allowed_by_globs(rel, includes, excludes):
            continue
        base, abs_path = resolve_root_and_abs(root, rel)
        for h in search_in_file(abs_path, rel, pattern, case_sensitive, mhpf):
            # anchors only (no snippet by default)
            hits.append({"anchor": make_anchor(rel, h["line"], 0)})
        scanned += 1
        if len(hits) >= limit * 2:  # small buffer before pagination
            break

    # Deterministic ordering
    hits.sort(key=lambda x: (x["anchor"]["path"], x["anchor"]["start_line"]))

    page, total, next_c = paginate_list(hits, limit, p.get("cursor"))
    return {
        "operation": "search",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "stats": {"scanned_files": scanned}
    }
