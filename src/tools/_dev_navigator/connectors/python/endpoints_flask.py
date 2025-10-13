import ast
from typing import List, Dict

from ...services.anchors import make_anchor

HTTP_METHODS = {"GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"}


def _get_str(node: ast.AST):
    if isinstance(node, ast.Str):
        return node.s
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_endpoints(py_code: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    try:
        tree = ast.parse(py_code)
    except Exception:
        return items

    for node in ast.walk(tree):  # iterative traversal (non-recursive)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in getattr(node, 'decorator_list', []) or []:
                # @app.route('/path', methods=['GET','POST'])
                if isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'route':
                    route_path = None
                    methods = None
                    if dec.args:
                        p = _get_str(dec.args[0])
                        if p is not None:
                            route_path = p
                    for kw in dec.keywords or []:
                        if kw.arg == 'methods' and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = []
                            for elt in kw.value.elts:
                                val = _get_str(elt)
                                if isinstance(val, str):
                                    methods.append(val.upper())
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

    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
