import re
from typing import List, Dict

from ...services.anchors import make_anchor

# Minimal Express.js endpoints extractor
# Matches: app.get('/path', ...), router.post('/x', ...)

# Use a backreference to the same quote captured in group 3
ROUTE_CALL = re.compile(r"\b(app|router)\.(get|post|put|delete|patch|options|head)\s*\(\s*(['\"])\/?([^'\"]*)\3")


def extract_endpoints_express(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items
    for i, line in enumerate(text.splitlines(), start=1):
        for m in ROUTE_CALL.finditer(line):
            method = m.group(2).upper()
            path = "/" + m.group(4)
            items.append({
                "kind": "http",
                "method": method,
                "path_or_name": path,
                "source_anchor": make_anchor(relpath, i, 0),
                "framework_hint": "express"
            })
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
