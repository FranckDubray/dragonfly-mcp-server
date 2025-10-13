import os
from typing import List, Dict

TEST_DIR_HINTS = {"tests", "test"}


def inventory_tests(root: str, paths: List[str]) -> List[Dict]:
    items: List[Dict] = []
    for rel in paths:
        base = os.path.basename(rel)
        parent = os.path.basename(os.path.dirname(rel))
        is_test = (
            base.startswith("test_") or base.endswith("_test.py") or parent.lower() in TEST_DIR_HINTS
        ) and base.endswith(".py")
        if is_test:
            items.append({"path": rel, "frameworks": ["pytest"], "anchor": {"path": rel, "start_line": 1, "start_col": 0}})
    items.sort(key=lambda x: x["path"])
    return items
