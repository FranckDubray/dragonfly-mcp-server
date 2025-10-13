from typing import Any, Dict, List
import os

from ..services.pagination import paginate_list
from ..services.pathing import resolve_root_and_abs
from ..services.fs_scanner import iter_files, read_text_head
from ..services.globber import allowed_by_globs
from ..services.budget_broker import compute_effective_budgets
from ..connectors.python.endpoints_fastapi import extract_endpoints as fe_fastapi
from ..connectors.python.endpoints_flask import extract_endpoints as fe_flask
from ..connectors.python.endpoints_django import extract_endpoints as fe_django


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    includes = p.get("glob_include") or []
    excludes = p.get("glob_exclude") or []

    eff = compute_effective_budgets(p)
    limit = eff["limit"]

    root = p["path"]
    scope_path = p.get("scope_path")

    items: List[Dict[str, Any]] = []
    scanned = 0
    for rel, _size in iter_files(root, scope_path, eff["max_files_scanned"]):
        if not allowed_by_globs(rel, includes, excludes):
            continue
        if not rel.endswith('.py'):
            continue
        base, abs_path = resolve_root_and_abs(root, rel)
        text = read_text_head(abs_path, eff["max_bytes_per_file"])
        # Aggregate endpoints from multiple paradigms
        items.extend(fe_fastapi(text, rel))
        items.extend(fe_flask(text, rel))
        # Django urls.py only
        if os.path.basename(rel) == 'urls.py':
            items.extend(fe_django(text, rel))
        scanned += 1
        if len(items) >= limit * 2:
            break

    # Deterministic order: path asc then method
    items.sort(key=lambda x: (x.get("path_or_name",""), x.get("method","")))

    page, total, next_c = paginate_list(items, limit, p.get("cursor"))
    return {
        "operation": "endpoints",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "stats": {"scanned_files": scanned}
    }
