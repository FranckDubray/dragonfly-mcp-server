from __future__ import annotations
import os
from typing import Dict, Any, List

ORDER = ["spec", "bootstrap", "api", "core", "validators", "utils", "services", "readme"]


def build_context_pack(files: List[str], strategy: str, max_bytes_per_file: int, max_total_context_bytes: int, fields: str) -> Dict[str, Any]:
    # Classify files
    classified: Dict[str, List[str]] = {k: [] for k in ORDER}
    for p in files:
        name = os.path.basename(p).lower()
        if "/tool_specs/" in p.replace("\\", "/") or name.endswith('.json'):
            classified["spec"].append(p)
        elif p.endswith(".py") and "/tools/_" in p.replace("\\", "/") and name == "api.py":
            classified["api"].append(p)
        elif p.endswith(".py") and "/tools/_" in p.replace("\\", "/") and name == "core.py":
            classified["core"].append(p)
        elif p.endswith(".py") and "/tools/_" in p.replace("\\", "/") and name == "validators.py":
            classified["validators"].append(p)
        elif p.endswith(".py") and "/tools/_" in p.replace("\\", "/") and name == "utils.py":
            classified["utils"].append(p)
        elif "/services/" in p.replace("\\", "/"):
            classified["services"].append(p)
        elif p.endswith(".md"):
            classified["readme"].append(p)
        elif p.endswith(".py"):
            classified["bootstrap"].append(p)
        else:
            classified.setdefault("services", []).append(p)

    ordered_files: List[str] = []
    for k in ORDER:
        ordered_files.extend(sorted(classified.get(k, [])))

    manifest: List[Dict[str, Any]] = []
    chunks: List[Dict[str, Any]] = []
    total_bytes = 0

    for path in ordered_files:
        try:
            size = os.path.getsize(path)
        except Exception:
            continue
        entry = {"path": path, "size": size}
        manifest.append(entry)
        if size <= 0:
            continue
        # clamp per file
        to_read = min(size, max_bytes_per_file)
        if total_bytes + to_read > max_total_context_bytes:
            # stop if global cap reached
            break
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read(to_read)
        except Exception:
            continue
        chunks.append({"path": path, "content": content})
        total_bytes += len(content.encode("utf-8", errors="ignore"))

    return {
        "manifest": manifest,
        "chunks": chunks,
        "total_bytes": total_bytes,
        "truncated": total_bytes >= max_total_context_bytes,
    }
