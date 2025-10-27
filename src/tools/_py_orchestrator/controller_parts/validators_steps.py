
import ast
from pathlib import Path
from typing import List, Optional, Tuple
from .constants import ALLOWED_IMPORTS
from .errors import make_error as _err, ValidationError

# Compact AST validator (<7KB)

def ast_validate_step(file_path: Path, func_name: str, kind: str) -> Tuple[List[str], List[str], Optional[str], Optional[str]]:
    src = file_path.read_text(encoding='utf-8')
    tree = ast.parse(src, filename=str(file_path))
    next_targets: List[str] = []
    exit_targets: List[str] = []
    call_count = 0
    call_kind: Optional[str] = None
    call_target: Optional[str] = None

    class V(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import):
            for a in node.names:
                if a.name.split('.')[0] not in ALLOWED_IMPORTS:
                    raise _err("Forbidden import", code="E110", file_path=file_path, lineno=node.lineno,
                               rule="No imports in step/cond (py_orch/typing only)", fix="Use env.tool/transform", example="env.tool('date')")
        def visit_ImportFrom(self, node: ast.ImportFrom):
            if (node.module or '').split('.')[0] not in ALLOWED_IMPORTS:
                raise _err("Forbidden import-from", code="E111", file_path=file_path, lineno=node.lineno,
                           rule="No imports in step/cond", fix="Use env.tool/transform", example="env.transform('x')")
        def visit_FunctionDef(self, node: ast.FunctionDef):
            nonlocal call_count, call_kind, call_target
            if node.name != func_name:
                return
            for n in ast.walk(node):
                if isinstance(n, ast.While):
                    raise _err("Forbidden while", code="E200", file_path=file_path, lineno=n.lineno,
                               rule="No loops", fix="Split steps", example="Next('N')")
                if isinstance(n, ast.For):
                    raise _err("Forbidden for", code="E201", file_path=file_path, lineno=n.lineno,
                               rule="No loops", fix="Map via transform", example="template_map")
                if isinstance(n, ast.With):
                    raise _err("Forbidden with", code="E202", file_path=file_path, lineno=n.lineno,
                               rule="No direct I/O", fix="Use MCP tools", example="http_client")
                if isinstance(n, ast.Try):
                    raise _err("Forbidden try", code="E203", file_path=file_path, lineno=n.lineno,
                               rule="Let orchestrator handle", fix="Split logic", example="Exit('warn')")
                # Steps cannot contain conditionals — branching must be explicit via @cond
                if kind == 'step' and isinstance(n, (ast.If, ast.IfExp)):
                    raise _err("Forbidden conditional in step", code="E204", file_path=file_path, lineno=getattr(n, 'lineno', node.lineno),
                               rule="No 'if/elif/else' or ternary inside @step. Use a separate @cond for branching.",
                               fix="Move the decision into an @cond function that returns Next/Exit.",
                               example="@cond\ndef DECIDE(worker, cycle, env):\n    return Next('A') if cond else Next('B')")
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'env':
                        if f.attr not in {'tool','transform'}:
                            raise _err("Forbidden env attr", code="E210", file_path=file_path, lineno=n.lineno,
                                       rule="Only env.tool/transform", fix="Use env.tool/transform", example="env.tool('date')")
                        call_count += 1
                        # Enforce literal tool/transform kind for explicit graphs
                        if not (n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                            raise _err("Dynamic env.tool/transform target", code="E232", file_path=file_path, lineno=n.lineno,
                                       rule="env.tool/transform first argument must be a string literal.",
                                       fix="Hardcode the tool/transform kind and branch via @cond if needed.",
                                       example="env.tool('date', operation='now')")
                        if call_kind is None:
                            call_kind = f.attr
                            call_target = n.args[0].value
                    elif isinstance(f, ast.Name) and f.id in {'open','eval','exec','__import__'}:
                        raise _err("Forbidden call", code="E220", file_path=file_path, lineno=n.lineno,
                                   rule="No low-level/eval", fix="Use MCP tools", example="env.tool('date')")
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name):
                    fn = n.value.func.id
                    # Enforce literal static target for Next/Exit (avoid hidden branching)
                    if fn in {'Next','Exit'}:
                        if len(n.value.args) != 1 or not isinstance(n.value.args[0], ast.Constant) or not isinstance(n.value.args[0].value, str):
                            raise _err("Dynamic Next/Exit target", code="E242", file_path=file_path, lineno=n.lineno,
                                       rule="Next/Exit must use a string literal target.", fix="Use @cond to compute target", example="Next('STEP_B')")
                    if fn == 'Next' and len(n.value.args) == 1 and isinstance(n.value.args[0], ast.Constant):
                        next_targets.append(str(n.value.args[0].value))
                    if fn == 'Exit' and len(n.value.args) == 1 and isinstance(n.value.args[0], ast.Constant):
                        exit_targets.append(str(n.value.args[0].value))
            # Cardinality rules
            if kind == 'step' and call_count != 1:
                raise _err(f"Step '{func_name}' must call exactly one env.tool/env.transform (found {call_count}).",
                           code="E230", file_path=file_path, lineno=getattr(node, 'lineno', 0),
                           rule="1 call per step", fix="Split into steps", example="env.tool('date'); Next('B')")
            if kind == 'step' and (len(next_targets) + len(exit_targets)) != 1:
                raise _err(
                    f"Step '{func_name}' must have exactly one outgoing transition (found Next:{len(next_targets)} Exit:{len(exit_targets)}).",
                    code="E241", file_path=file_path, lineno=getattr(node, 'lineno', 0),
                    rule="1 outgoing edge for steps",
                    fix="Move any branching into an @cond function placed before or after the step.",
                    example="@cond\ndef DECIDE(...): return Next('X') if cond else Next('Y')",
                )
            if kind == 'cond' and call_count != 0:
                raise _err(f"Conditional '{func_name}' must not call env.tool/env.transform (found {call_count}).",
                           code="E231", file_path=file_path, lineno=getattr(node, 'lineno', 0),
                           rule="0 call in cond", fix="Move calls to steps", example="Exit('success')")
            if not next_targets and not exit_targets:
                raise _err(f"Function '{func_name}' must return Next('...') or Exit('...').",
                           code="E240", file_path=file_path, lineno=getattr(node, 'lineno', 0),
                           rule="Define next transition", fix="Add Next/Exit", example="Next('STEP_B')")

    V().visit(tree)
    return next_targets, exit_targets, call_kind, call_target
