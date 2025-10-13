import ast
from typing import List, Dict

from ...services.anchors import make_anchor

# Django routes are typically declared in urls.py using path()/re_path()
SUPPORTED = {"path", "re_path"}


def extract_endpoints(py_code: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    try:
        tree = ast.parse(py_code)
    except Exception:
        return items

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            func_name = getattr(node.func, 'id', None) or getattr(getattr(node.func, 'attr', None), 'id', None)
            # Simplified: only match direct calls to path()/re_path()
            name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
            if name in SUPPORTED:
                route_path = None
                if node.args and isinstance(node.args[0], ast.Str):
                    route_path = node.args[0].s
                if route_path:
                    items.append({
                        "kind": "http",
                        "method": "GET",
                        "path_or_name": route_path,
                        "source_anchor": make_anchor(relpath, node.lineno, 0),
                        "framework_hint": "django"
                    })
            self.generic_visit(node)

    Visitor().visit(tree)
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
