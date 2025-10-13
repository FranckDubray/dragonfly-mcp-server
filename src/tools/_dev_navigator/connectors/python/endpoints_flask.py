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

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            for dec in node.decorator_list:
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
                                    "source_anchor": make_anchor(relpath, node.lineno, 0),
                                    "framework_hint": "flask"
                                })
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self.visit_FunctionDef(node)

    Visitor().visit(tree)
    items.sort(key=lambda x: (x["path_or_name"], x["method"]))
    return items
