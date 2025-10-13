import ast
from typing import List, Dict

from ...services.anchors import make_anchor

# Django routes are typically declared in urls.py using path()/re_path()
SUPPORTED = {"path", "re_path"}


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

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # Simplified: only match direct calls to path()/re_path()
            name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
            if name in SUPPORTED:
                route_path = None
                if node.args:
                    p = _get_str(node.args[0])
                    if p is not None:
                        route_path = p
                if route_path:
                    items.append({
                        "kind": "http",
                        "method": "ANY",  # method cannot be inferred from urls.py alone
                        "path_or_name": route_path,
                        "source_anchor": make_anchor(relpath, node.lineno, 0),
                        "framework_hint": "django"
                    })
            self.generic_visit(node)

    Visitor().visit(tree)
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
