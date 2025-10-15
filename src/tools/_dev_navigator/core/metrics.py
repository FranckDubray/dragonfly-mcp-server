from typing import Any, Dict
import os

from ..services.fs_scanner import iter_files, read_text_head
from ..services.lang_detect import language_from_path
from ..services.budget_broker import compute_effective_budgets
from ..connectors.python.sloc_estimator import estimate_sloc
from ..connectors.python.outline_ast import outline_file
from ..release_index import reader_paths as P
from ..release_index import reader_queries as Q


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return compact repository metrics under strict budgets:
    - total_files, total_bytes (best-effort)
    - files_by_language [{name, files}]
    - sloc_estimate per language (python/js/ts/html/md/go; others = None)
    - functions_estimate: total functions (python only for now)
    Notes:
      * Uses head-limited reads (max_bytes_per_file)
      * Scans up to max_files_scanned files
    """
    eff = compute_effective_budgets(p)
    root = p["path"]
    scope_path = p.get("scope_path")

    # INDEX-FIRST fast path
    if p.get("use_release_index", True):
        db_path, err = P.resolve_index_db(root, p.get("release_tag"), p.get("commit_hash"))
        if db_path:
            conn = P._open_ro(db_path)
            try:
                dir_stats = Q.query_dir_stats_all(conn)
                try:
                    func_count = Q.query_functions_count(conn)
                except Exception:
                    func_count = 0
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            total_files = sum(int(r["files"]) for r in dir_stats)
            total_bytes = sum(int(r["bytes"]) for r in dir_stats)
            data = {
                "total_files": int(total_files),
                "total_bytes": int(total_bytes),
                "files_by_language": [],
                "sloc_estimate": [],
                "functions_estimate": {"python": int(func_count), "total": int(func_count)}
            }
            return {
                "operation": "metrics",
                "data": data,
                "returned_count": 0,
                "total_count": 0,
                "truncated": False,
                "stats": {"source": "release_index"}
            }

    files_by_lang: Dict[str, int] = {}
    sloc_by_lang: Dict[str, int] = {}
    func_count_python = 0
    total_files = 0
    total_bytes = 0

    scanned = 0
    for rel, size in iter_files(root, scope_path, eff["max_files_scanned"]):
        lang = language_from_path(rel) or "other"
        files_by_lang[lang] = files_by_lang.get(lang, 0) + 1
        total_files += 1
        total_bytes += int(size)
        # Head-limited content read
        abs_path = os.path.join(root, rel)
        try:
            text = read_text_head(abs_path, eff["max_bytes_per_file"])  # head only
        except Exception:
            text = ""
        # SLOC estimation for supported languages
        if lang in {"python", "javascript", "typescript", "html", "markdown", "go"}:
            sloc_by_lang[lang] = sloc_by_lang.get(lang, 0) + estimate_sloc(lang, text)
        # Functions count (python only, via outline)
        if lang == "python":
            try:
                outlines = outline_file(text, rel)
                func_count_python += sum(1 for it in outlines if it.get("kind") == "function")
            except Exception:
                pass
        scanned += 1
        if scanned >= eff["max_files_scanned"]:
            break

    files_by_language = [{"name": k, "files": v} for k, v in files_by_lang.items()]
    files_by_language.sort(key=lambda x: (-x["files"], x["name"]))

    # Prepare sloc estimates in same order
    sloc_estimate = []
    for it in files_by_language:
        lang = it["name"]
        sloc_estimate.append({"language": lang, "sloc": int(sloc_by_lang.get(lang)) if lang in sloc_by_lang else None})

    data = {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "files_by_language": files_by_language[:10],
        "sloc_estimate": sloc_estimate[:10],
        "functions_estimate": {
            "python": int(func_count_python),
            "total": int(func_count_python)
        }
    }

    return {
        "operation": "metrics",
        "data": data,
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {"scanned_files": scanned}
    }
