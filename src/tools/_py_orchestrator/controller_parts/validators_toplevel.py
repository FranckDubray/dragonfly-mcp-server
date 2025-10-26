import ast
from pathlib import Path
from .constants import ALLOWED_IMPORTS
from .errors import make_error as _err, ValidationError
from typing import List

def validate_module_toplevel(file_path: Path, allowed_assign_names: List[str]) -> None:
    src = file_path.read_text(encoding='utf-8')
    tree = ast.parse(src, filename=str(file_path))
    seen_docstring = False
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            # Top-level docstring allowed once (first statement only)
            if i == 0 and not seen_docstring:
                seen_docstring = True
                continue
            else:
                raise _err(
                    f"Forbidden top-level expression.",
                    code="E100",
                    file_path=file_path,
                    lineno=getattr(node, 'lineno', 0),
                    rule="Only one module docstring is allowed at top-level.",
                    fix="Remove expressions at top-level. Keep only docstring, assignments to allowed names, and defs.",
                    example="""# Good\n\"\"\"Doc\"\"\"\nPROCESS = ...\n\n# Bad\nprint('hi')""",
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] not in ALLOWED_IMPORTS:
                    raise _err(
                        f"Forbidden import '{alias.name}'.",
                        code="E110",
                        file_path=file_path,
                        lineno=getattr(node, 'lineno', 0),
                        rule="Imports are restricted to safe runtime helpers.",
                        fix="Remove the import and use py_orch runtime (step/cond/Next/Exit) or transforms/tools via env.",
                        example="from py_orch import step, cond, Next, Exit",
                    )
            continue
        if isinstance(node, ast.ImportFrom):
            if (node.module or '').split('.')[0] not in ALLOWED_IMPORTS:
                raise _err(
                    f"Forbidden import-from '{node.module}'.",
                    code="E111",
                    file_path=file_path,
                    lineno=getattr(node, 'lineno', 0),
                    rule="Imports are restricted to safe runtime helpers.",
                    fix="Remove the import-from and use py_orch runtime.",
                    example="from py_orch import step, Next, Exit",
                )
            continue
        if isinstance(node, ast.Assign):
            ok = True
            for t in node.targets:
                if not (isinstance(t, ast.Name) and t.id in allowed_assign_names):
                    ok = False
                    break
            if not ok:
                raise _err(
                    "Forbidden top-level assignment.",
                    code="E120",
                    file_path=file_path,
                    lineno=getattr(node, 'lineno', 0),
                    rule=f"Only assignments to {allowed_assign_names} are allowed at module top-level.",
                    fix="Move logic into @step/@cond or keep only PROCESS/SUBGRAPH definitions.",
                    example="PROCESS = Process(...)",
                )
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        raise _err(
            "Forbidden top-level statement.",
            code="E121",
            file_path=file_path,
            lineno=getattr(node, 'lineno', 0),
            rule="Top-level must contain only docstring, allowed assignments, and defs.",
            fix="Remove statements (if/for/with/try...) from top-level.",
            example="# Good: only defs at top-level\n@step\ndef F(...): ...",
        )
