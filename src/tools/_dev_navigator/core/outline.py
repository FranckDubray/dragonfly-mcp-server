from typing import Any, Dict, List
import os

from ..services.pagination import paginate_list
from ..services.pathing import resolve_root_and_abs
from ..services.fs_scanner import iter_files, read_text_head
from ..services.globber import allowed_by_globs
from ..services.budget_broker import compute_effective_budgets
from ..services.anchors import make_anchor
from ..services.lang_detect import language_from_path
from ..connectors.python.outline_ast import outline_file as outline_py
from ..connectors.javascript.outline_js import outline_file_js
from ..connectors.go.outline_go import outline_file_go


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    includes = p.get("glob_include") or []
    excludes = p.get("glob_exclude") or []

    eff = compute_effective_budgets(p)
    limit = eff["limit"]

    root = p["path"]
    scope_path = p.get("scope_path")

    # Collect minimal outlines (anchors-only) across supported languages
    items: List[Dict[str, Any]] = []
    scanned = 0
    for rel, _size in iter_files(root, scope_path, eff["max_files_scanned"]):
        if not allowed_by_globs(rel, includes, excludes):
            continue
        base, abs_path = resolve_root_and_abs(root, rel)
        text = read_text_head(abs_path, eff["max_bytes_per_file"])
        lang = language_from_path(rel)
        outlines: List[Dict[str, Any]] = []
        if lang == "python":
            outlines = outline_py(text, rel)
        elif lang in {"javascript", "typescript"}:
            outlines = outline_file_js(text, rel)
        elif lang == "go":
            outlines = outline_file_go(text, rel)
        # else: unsupported -> no outlines
        if outlines:
            items.append({"path": rel, "symbols": outlines})
        scanned += 1
        if len(items) >= limit * 2:
            break

    # Deterministic ordering
    items.sort(key=lambda x: x["path"]) 

    page, total, next_c = paginate_list(items, limit, p.get("cursor"))
    # fs_requests hint: heads of current page files
    fs_requests = [{"path": it["path"], "ranges": [{"start_line": 1, "end_line": 80}]} for it in page[:5]]
    return {
        "operation": "outline",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "fs_requests": fs_requests,
        "stats": {"scanned_files": scanned}
    }
