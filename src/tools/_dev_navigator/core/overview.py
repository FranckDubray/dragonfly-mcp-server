from typing import Any, Dict, List, Tuple
import os

from ..services.fs_scanner import iter_files, read_text_head
from ..services.lang_detect import language_from_path
from ..services.budget_broker import compute_effective_budgets
from ..connectors.python.sloc_estimator import estimate_sloc
from ..connectors.python.outline_ast import outline_file
from ..release_index import reader_paths as P
from ..release_index import reader_queries as Q

DOC_CANDIDATES = ("README", "CHANGELOG", "LICENSE")


def _detect_top_docs(root: str) -> List[Dict]:
    docs: List[Dict] = []
    try:
        for name in os.listdir(root):
            upper = name.upper()
            if any(upper.startswith(p) for p in DOC_CANDIDATES):
                full = os.path.join(root, name)
                try:
                    st = os.stat(full)
                    docs.append({"path": name, "bytes": int(st.st_size)})
                except OSError:
                    continue
    except Exception:
        pass
    docs.sort(key=lambda x: x["path"])  # deterministic
    return docs[:3]


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    root = p["path"]
    eff = compute_effective_budgets(p)

    # INDEX-FIRST: use index when available
    if p.get("use_release_index", True):
        db_path, err = P.resolve_index_db(root, p.get("release_tag"), p.get("commit_hash"))
        if db_path:
            conn = P._open_ro(db_path)
            try:
                files = Q.query_files_all(conn, limit=10000)
                outlines = Q.query_outline_samples(conn, per_file=5, max_files=3)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            # Languages by extension (best-effort)
            lang_counts: Dict[str, int] = {}
            for f in files:
                lang = language_from_path(f["relpath"]) or "other"
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            languages = [{"name": k, "files": v} for k, v in lang_counts.items()]
            languages.sort(key=lambda x: (-x["files"], x["name"]))

            # Top-level key docs
            key_files = [
                {"path": f["relpath"], "bytes": int(f["size"])}
                for f in files
                if os.sep not in f["relpath"] and any(f["relpath"].upper().startswith(x) for x in DOC_CANDIDATES)
            ][:3]

            data = {
                "languages": languages[:5],
                "key_files": key_files,
                "representative_outlines": outlines[:3]
            }

            return {
                "operation": "overview",
                "data": data,
                "returned_count": 0,
                "total_count": 0,
                "truncated": False,
                "stats": {"source": "release_index"}
            }

    lang_counts: Dict[str, int] = {}
    sloc_total = 0
    outlines_sample: List[Dict] = []

    scanned = 0
    for rel, _size in iter_files(root, p.get("scope_path"), eff["max_files_scanned"]):
        lang = language_from_path(rel) or "other"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        if lang == "python" and len(outlines_sample) < 5:
            try:
                text = read_text_head(os.path.join(root, rel), eff["max_bytes_per_file"])  # head only
            except Exception:
                text = ""
            sloc_total += estimate_sloc("python", text)
            outlines = outline_file(text, rel)[:5]
            if outlines:
                outlines_sample.append({"path": rel, "symbols": outlines})
        scanned += 1
        if scanned >= eff["max_files_scanned"]:
            break

    languages = [{"name": k, "files": v} for k, v in lang_counts.items()]
    languages.sort(key=lambda x: (-x["files"], x["name"]))

    key_files = _detect_top_docs(root)

    data = {
        "languages": languages[:5],
        "key_files": key_files,
        "representative_outlines": outlines_sample[:3]
    }

    return {
        "operation": "overview",
        "data": data,
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {"scanned_files": scanned}
    }
