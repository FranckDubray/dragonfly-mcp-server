import ast
from typing import Dict, List, Tuple

from ..services.anchors import make_anchor

MAX_AST_DEPTH = 5000


def _is_upper_name(name: str) -> bool:
    return bool(name) and name.isupper()


def extract_symbols_calls_imports(py_code: str, relpath: str) -> Dict[str, List[Dict]]:
    try:
        tree = ast.parse(py_code)
    except Exception:
        return {"symbols": [], "calls": [], "imports": []}

    symbols: List[Dict] = []
    calls: List[Dict] = []
    imports: List[Dict] = []

    module = relpath[:-3].replace("/", ".").replace("\\", ".") if relpath.endswith(".py") else relpath
    scope: List[Tuple[str, str]] = []  # (kind, name)

    stack: List[Tuple[ast.AST, int]] = [(tree, 0)]

    while stack:
        node, depth = stack.pop()
        if depth > MAX_AST_DEPTH:
            continue

        if isinstance(node, ast.ClassDef):
            fq = ".".join([module] + [nm for k, nm in scope if k == "class"] + [node.name])
            symbols.append({
                "name": node.name,
                "fqname": fq,
                "symbol_key": fq.lower(),
                "kind": "class",
                "lang": "python",
                "anchor": make_anchor(relpath, getattr(node, "lineno", 1), 0, getattr(node, "end_lineno", getattr(node, "lineno", 1)), 0),
                "signature": None,
                "container_kind": None,
                "container_name": None,
            })
            scope.append(("class", node.name))
            for child in ast.iter_child_nodes(node):
                stack.append((child, depth + 1))
            scope.pop()
            continue

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            in_class = any(k == "class" for k, _ in scope)
            fq = ".".join([module] + [nm for k, nm in scope if k == "class"] + [node.name])
            symbols.append({
                "name": node.name,
                "fqname": fq,
                "symbol_key": fq.lower(),
                "kind": "method" if in_class else "function",
                "lang": "python",
                "anchor": make_anchor(relpath, getattr(node, "lineno", 1), 0, getattr(node, "end_lineno", getattr(node, "lineno", 1)), 0),
                "signature": None,
                "container_kind": ("class" if in_class else None),
                "container_name": next((nm for k, nm in reversed(scope) if k == "class"), None) if in_class else None,
            })
            scope.append(("function", node.name))
            for child in ast.iter_child_nodes(node):
                stack.append((child, depth + 1))
            scope.pop()
            continue

        if isinstance(node, ast.Assign):
            if not scope:
                for t in node.targets:
                    name = None
                    if isinstance(t, ast.Name):
                        name = t.id
                    elif isinstance(t, ast.Attribute):
                        name = t.attr
                    if name and _is_upper_name(name):
                        fq = f"{module}.{name}"
                        symbols.append({
                            "name": name,
                            "fqname": fq,
                            "symbol_key": fq.lower(),
                            "kind": "var",
                            "lang": "python",
                            "anchor": make_anchor(relpath, getattr(node, "lineno", 1), 0, getattr(node, "end_lineno", getattr(node, "lineno", 1)), 0),
                            "signature": None,
                            "container_kind": None,
                            "container_name": None,
                        })
            continue

        if isinstance(node, ast.Import):
            for alias in node.names:
                to_key = alias.asname or alias.name
                imports.append({"from": None, "to_key": to_key, "kind": "import", "raw": f"import {alias.name}"})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                to_key = f"{mod}.{alias.name}" if mod else alias.name
                imports.append({"from": mod, "to_key": to_key, "kind": "from", "raw": f"from {mod} import {alias.name}"})
        elif isinstance(node, ast.Call):
            callee = None
            func = node.func
            if isinstance(func, ast.Name):
                callee = func.id
            elif isinstance(func, ast.Attribute):
                callee = func.attr
            if callee:
                caller_sym = next((nm for k, nm in reversed(scope) if k in ("function", "method")), None)
                calls.append({
                    "callee_key": callee.lower(),
                    "caller_symbol_name": caller_sym,
                    "anchor": make_anchor(relpath, getattr(node, "lineno", 1), 0),
                    "args_shape": None,
                    "is_test": 1 if "test" in relpath.lower() else 0,
                })

        for child in ast.iter_child_nodes(node):
            stack.append((child, depth + 1))

    return {"symbols": symbols, "calls": calls, "imports": imports}
