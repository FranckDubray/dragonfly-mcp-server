import re
from typing import List, Dict

from ...services.anchors import make_anchor

# Simple JS/TS outline extractor (regex-based, head-only friendly)
# Detects: function declarations, exported functions, const arrow functions, classes

FUNC_DECL = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
ARROW_CONST = re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*=>")
CLASS_DECL = re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b")


def outline_file_js(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items
    for i, line in enumerate(text.splitlines(), start=1):
        m = FUNC_DECL.search(line)
        if m:
            items.append({
                "name": m.group(1),
                "kind": "function",
                "anchor": make_anchor(relpath, i, 0)
            })
            continue
        m = ARROW_CONST.search(line)
        if m:
            items.append({
                "name": m.group(1),
                "kind": "function",
                "anchor": make_anchor(relpath, i, 0)
            })
            continue
        m = CLASS_DECL.search(line)
        if m:
            items.append({
                "name": m.group(1),
                "kind": "class",
                "anchor": make_anchor(relpath, i, 0)
            })
    # Deterministic by line
    items.sort(key=lambda x: (x["anchor"]["start_line"], x.get("name","")))
    return items
