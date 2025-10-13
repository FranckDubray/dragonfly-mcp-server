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

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            for dec in node.decorator_list:
                method = None
                path = None
                if isinstance(dec, ast.Call):
                    # app.get("/path"), router.post("/path")
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
                        "source_anchor": make_anchor(relpath, node.lineno, 0),
                        "framework_hint": "fastapi"
                    })
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self.visit_FunctionDef(node)  # same handling

    Visitor().visit(tree)
    # deterministic ordering
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
