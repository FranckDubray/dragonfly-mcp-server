import ast
from typing import List, Dict

from ...services.anchors import make_anchor


def outline_file(py_code: str, relpath: str) -> List[Dict]:
    """Return a minimal outline: functions/classes with anchors. No bodies returned.
    Falls back to empty on parse errors.
    """
    items: List[Dict] = []
    try:
        tree = ast.parse(py_code)
    except Exception:
        return items

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            items.append({
                "name": node.name,
                "kind": "function",
                "anchor": make_anchor(relpath, node.lineno, 0, getattr(node, 'end_lineno', node.lineno), 0)
            })
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            items.append({
                "name": node.name,
                "kind": "function",
                "anchor": make_anchor(relpath, node.lineno, 0, getattr(node, 'end_lineno', node.lineno), 0)
            })
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef):
            items.append({
                "name": node.name,
                "kind": "class",
                "anchor": make_anchor(relpath, node.lineno, 0, getattr(node, 'end_lineno', node.lineno), 0)
            })
            self.generic_visit(node)

    Visitor().visit(tree)
    # deterministic ordering by line
    items.sort(key=lambda x: (x["anchor"]["start_line"], x.get("name","")))
    return items
