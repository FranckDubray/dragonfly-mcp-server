import ast
from typing import List, Dict

from ...services.anchors import make_anchor

HTTP_METHODS = {"get","post","put","delete","patch","options","head"}


def extract_endpoints(py_code: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    try:
        tree = ast.parse(py_code)
    except Exception:
        return items
    try:
        for node in ast.walk(tree):  # iterative, non-recursive traversal
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in getattr(node, 'decorator_list', []) or []:
                    method = None
                    path = None
                    if isinstance(dec, ast.Call):
                        func = dec.func
                        if isinstance(func, ast.Attribute) and func.attr in HTTP_METHODS:
                            method = func.attr.upper()
                            if dec.args and isinstance(dec.args[0], ast.Str):
                                path = dec.args[0].s
                    if method and path:
                        items.append({
                            "kind": "http",
                            "method": method,
                            "path_or_name": path,
                            "source_anchor": make_anchor(relpath, getattr(node, 'lineno', 1), 0),
                            "framework_hint": "fastapi"
                        })
    except RecursionError:
        return items
    # deterministic ordering
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
