from __future__ import annotations
from typing import Dict, Any, List, Tuple, Set
from pathlib import Path
import ast

# Backend helper to extract tools/transforms directly from worker Python code
# Strategy:
#  - Resolve template for a worker_name via identity_api (fallbacks below)
#  - Scan workers/<template>/process.py and workers/<template>/subgraphs/*.py
#  - Parse AST and collect calls:
#       env.tool("<name>", ..., operation="<op>")
#       env.transform("<name>", ..., op="<op>")
#  - Return deterministic JSON structure for the SPA grid

async def get(worker_name: str, include_transforms: bool = False) -> Dict[str, Any]:
    template = await _resolve_template(worker_name)
    if not template:
        out: Dict[str, Any] = {"accepted": True, "status": "not_found_template", "worker": worker_name, "tools": []}
        if include_transforms:
            out["transforms"] = []
        return out

    base = _workers_base() / template
    if not base.exists():
        out = {"accepted": True, "status": "not_found_template_dir", "worker": worker_name, "template": template, "tools": []}
        if include_transforms:
            out["transforms"] = []
        return out

    files = _collect_files(base)
    tools_idx: Dict[str, Set[str]] = {}
    trans_idx: Dict[str, Set[str]] = {}

    for p in files:
        try:
            t, tr = _extract_from_py(p)
            for name, ops in t.items():
                tools_idx.setdefault(name, set()).update(ops)
            for name, ops in tr.items():
                trans_idx.setdefault(name, set()).update(ops)
        except Exception:
            # ignore a single file failure
            continue

    tools = [{"name": n, "operations": sorted(list(ops))} for n, ops in sorted(tools_idx.items(), key=lambda kv: kv[0].lower())]

    out: Dict[str, Any] = {
        "accepted": True,
        "status": "ok",
        "worker": worker_name,
        "template": template,
        "tools": tools,
    }
    if include_transforms:
        transforms = [{"name": n, "ops": sorted(list(ops))} for n, ops in sorted(trans_idx.items(), key=lambda kv: kv[0].lower())]
        out["transforms"] = transforms
    return out


async def _resolve_template(worker_name: str) -> str:
    """Resolve template from identity; fallback to DB KV and slug heuristic."""
    # 1) Try identity_api (authoritative)
    try:
        from .identity_api import get_identity
        ident = await get_identity(worker_name)
        tpl = str(ident.get("template") or "").strip()
        if tpl:
            return tpl
    except Exception:
        pass

    # 2) Fallback: DB KV 'worker_file' -> parse workers/<template>/process.py
    try:
        from src.tools._py_orchestrator.api_spawn import db_path_for_worker
        from src.tools._py_orchestrator.db import get_state_kv
        dbp = db_path_for_worker(worker_name)
        wf_prev = get_state_kv(dbp, worker_name, 'worker_file') or ''
        wf_prev = str(wf_prev).strip()
        if wf_prev and wf_prev.startswith('workers/') and wf_prev.endswith('/process.py'):
            # workers/<template>/process.py -> <template>
            rel = Path(wf_prev)
            return rel.parts[1] if len(rel.parts) >= 2 else ''
    except Exception:
        pass

    # 3) Heuristic: try to find a workers/<template> directory that matches the prefix of worker_name
    try:
        wb = _workers_base()
        if wb.exists():
            candidates = [d.name for d in wb.iterdir() if d.is_dir() and not d.name.startswith('.')]
            # pick the longest directory name that is a prefix of worker_name or worker_name startswith '<tpl>_'
            best = ''
            for tpl in candidates:
                if worker_name == tpl or worker_name.startswith(tpl + '_'):
                    if len(tpl) > len(best):
                        best = tpl
            if best:
                return best
    except Exception:
        pass

    return ''


def _project_root() -> Path:
    try:
        from config import find_project_root
        return Path(find_project_root())
    except Exception:
        return Path.cwd()


def _workers_base() -> Path:
    return _project_root() / 'workers'


def _collect_files(base: Path) -> List[Path]:
    files: List[Path] = []
    # process.py at root
    p = base / 'process.py'
    if p.exists():
        files.append(p)
    # subgraphs/*.py
    sg = base / 'subgraphs'
    if sg.exists():
        for f in sorted(sg.glob('*.py')):
            files.append(f)
    return files


def _extract_from_py(path: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Return (tools, transforms) indexes for a single file.
    tools:    name -> set(operations)
    transforms: name -> set(ops)
    """
    try:
        src = path.read_text(encoding='utf-8')
    except Exception:
        return {}, {}

    try:
        tree = ast.parse(src, filename=str(path))
    except Exception:
        return {}, {}

    tools: Dict[str, Set[str]] = {}
    transforms: Dict[str, Set[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(getattr(node, 'func', None), ast.Attribute):
            owner = getattr(node.func, 'value', None)
            if isinstance(owner, ast.Name) and owner.id == 'env':
                kind = node.func.attr  # 'tool' or 'transform' expected
                if kind not in {'tool', 'transform'}:
                    continue
                name = _const_str(_first_arg(node)) or ''
                if not name:
                    continue
                if kind == 'tool':
                    op = _kw_str(node, 'operation') or ''
                    tools.setdefault(name, set())
                    if op:
                        tools[name].add(op)
                else:
                    op = _kw_str(node, 'op') or ''
                    transforms.setdefault(name, set())
                    if op:
                        transforms[name].add(op)
    return tools, transforms


def _first_arg(call: ast.Call):
    try:
        return call.args[0]
    except Exception:
        return None


def _kw_str(call: ast.Call, key: str) -> str | None:
    try:
        for kw in call.keywords or []:
            if kw.arg == key and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
    except Exception:
        return None
    return None


def _const_str(node) -> str | None:
    try:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
    except Exception:
        return None
    return None
