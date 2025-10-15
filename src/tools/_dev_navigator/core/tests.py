from typing import Any, Dict, List

from ..services.pagination import paginate_list
from ..services.budget_broker import compute_effective_budgets
from ..services.fs_scanner import iter_files
from ..services.globber import allowed_by_globs
from ..connectors.python.tests_inventory import inventory_tests
from ..release_index import reader_paths as P
from ..release_index import reader_queries as Q


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    includes = p.get("glob_include") or []
    excludes = p.get("glob_exclude") or []

    eff = compute_effective_budgets(p)
    limit = eff["limit"]

    root = p["path"]

    # INDEX-FIRST: list tests from the release index if available
    if p.get("use_release_index", True):
        db_path, err = P.resolve_index_db(root, p.get("release_tag"), p.get("commit_hash"))
        if db_path:
            conn = P._open_ro(db_path)
            try:
                files = Q.query_tests_files(conn, limit * 10)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            items = [{"path": rel, "frameworks": ["pytest"], "anchor": {"path": rel, "start_line": 1, "start_col": 0}} for rel in files]
            items.sort(key=lambda x: x["path"])  
            page, total, next_c = paginate_list(items, limit, p.get("cursor"))
            return {
                "operation": "tests",
                "data": page,
                "returned_count": len(page),
                "total_count": total,
                "truncated": next_c is not None,
                "next_cursor": next_c,
                "stats": {"source": "release_index"}
            }

    scope_path = p.get("scope_path")

    # Collect candidate file paths
    paths: List[str] = []
    scanned = 0
    for rel, _size in iter_files(root, scope_path, eff["max_files_scanned"]):
        if not allowed_by_globs(rel, includes, excludes):
            continue
        paths.append(rel)
        scanned += 1
        if len(paths) >= limit * 10:  # buffer before pagination
            break

    # Detect tests among collected paths
    tests = inventory_tests(root, paths)
    # Deterministic ordering
    tests.sort(key=lambda x: x["path"])  

    page, total, next_c = paginate_list(tests, limit, p.get("cursor"))
    return {
        "operation": "tests",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "stats": {"scanned_files": scanned}
    }
