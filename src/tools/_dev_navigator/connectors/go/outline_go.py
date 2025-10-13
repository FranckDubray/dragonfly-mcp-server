import re
from typing import List, Dict

from ...services.anchors import make_anchor

# Simple Go outline extractor for functions and types
FUNC_DECL = re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(")
TYPE_DECL = re.compile(r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+(struct|interface)\b")

MAX_ITEMS = 500


def outline_file_go(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items
    for i, line in enumerate(text.splitlines(), start=1):
        if len(items) >= MAX_ITEMS:
            break
        m = FUNC_DECL.search(line)
        if m:
            items.append({
                "name": m.group(1),
                "kind": "function",
                "anchor": make_anchor(relpath, i, 0)
            })
            continue
        m = TYPE_DECL.search(line)
        if m:
            items.append({
                "name": m.group(1),
                "kind": m.group(2),
                "anchor": make_anchor(relpath, i, 0)
            })
    items.sort(key=lambda x: (x["anchor"]["start_line"], x.get("name","")))
    return items
