from typing import Any, Dict, List, Tuple
import os

from ..services.fs_scanner import iter_files, read_text_head
from ..services.lang_detect import language_from_path
from ..services.budget_broker import compute_effective_budgets
from ..connectors.python.sloc_estimator import estimate_sloc
from ..connectors.python.outline_ast import outline_file

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
