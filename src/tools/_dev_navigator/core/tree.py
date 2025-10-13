from typing import Any, Dict, List, Tuple
import os

from ..services.pagination import paginate_list
from ..services.budget_broker import compute_effective_budgets
from ..services.fs_scanner import iter_files


def _accumulate_dirs(rel: str, size: int, max_depth: int) -> List[Tuple[str, int]]:
    parts = rel.split(os.sep)
    acc: List[Tuple[str, int]] = []
    for d in range(1, min(len(parts), max_depth) + 1):
        path = os.sep.join(parts[:d])
        acc.append((path, size))
    return acc


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    eff = compute_effective_budgets(p)
    limit = eff["limit"]
    max_depth = int(p.get("depth_for_tree", 3))

    root = p["path"]
    scope_path = p.get("scope_path")

    # Aggregate per-directory stats (files_count, bytes) within depth
    files_per_dir: Dict[str, int] = {}
    bytes_per_dir: Dict[str, int] = {}

    scanned = 0
    for rel, size in iter_files(root, scope_path, eff["max_files_scanned"]):
        for dpath, dsize in _accumulate_dirs(rel, size, max_depth):
            files_per_dir[dpath] = files_per_dir.get(dpath, 0) + 1
            bytes_per_dir[dpath] = bytes_per_dir.get(dpath, 0) + int(dsize)
        scanned += 1
        if scanned >= eff["max_files_scanned"]:
            break

    nodes = [{
        "path": d,
        "depth": d.count(os.sep) + 1,
        "files_count": files_per_dir.get(d, 0),
        "bytes": bytes_per_dir.get(d, 0)
    } for d in files_per_dir.keys()]

    # Deterministic order: shorter depth then path asc
    nodes.sort(key=lambda x: (x["depth"], x["path"]))

    page, total, next_c = paginate_list(nodes, limit, p.get("cursor"))
    return {
        "operation": "tree",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "stats": {"scanned_files": scanned}
    }
