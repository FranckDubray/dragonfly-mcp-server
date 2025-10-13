import ast
from typing import List, Dict

from ...services.anchors import make_anchor

HTTP_METHODS = {"GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"}


def extract_endpoints(py_code: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    try:
        tree = ast.parse(py_code)
    except Exception:
        return items

    try:
        for node in ast.walk(tree):  # iterative traversal (non-recursive)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in getattr(node, 'decorator_list', []) or []:
                    # @app.route('/path', methods=['GET','POST'])
                    if isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'route':
                        route_path = None
                        methods = None
                        if dec.args and isinstance(dec.args[0], ast.Str):
                            route_path = dec.args[0].s
                        for kw in dec.keywords or []:
                            if kw.arg == 'methods' and isinstance(kw.value, (ast.List, ast.Tuple)):
                                methods = []
                                for elt in kw.value.elts:
                                    if isinstance(elt, ast.Str):
                                        methods.append(elt.s.upper())
                        if route_path:
                            if not methods:
                                methods = ["GET"]
                            for m in methods:
                                if m in HTTP_METHODS:
                                    items.append({
                                        "kind": "http",
                                        "method": m,
                                        "path_or_name": route_path,
                                        "source_anchor": make_anchor(relpath, getattr(node, 'lineno', 1), 0),
                                        "framework_hint": "flask"
                                    })
    except RecursionError:
        return items

    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
