from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple
import ast, json

HANDLERS_SUBPKGS = ("transforms", "transforms_domain")
META_START = "TRANSFORM_META_START"
META_END = "TRANSFORM_META_END"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _extract_meta_block(src: str) -> Dict[str, Any] | None:
    """Parse a JSON meta block delimited by lines containing META_START/END markers.
    Expected format in file (at top):
    # TRANSFORM_META_START
    { "io_type": "list->list", "description": "...", "inputs": [...], "outputs": [...] }
    # TRANSFORM_META_END
    """
    if not src:
        return None
    lines = src.splitlines()
    start, end = -1, -1
    for i, ln in enumerate(lines):
        if META_START in ln:
            start = i + 1
            break
    if start == -1:
        return None
    for j in range(start, len(lines)):
        if META_END in lines[j]:
            end = j
            break
    if end == -1:
        return None
    blob = "\n".join(lines[start:end]).strip()
    try:
        return json.loads(blob) if blob else None
    except Exception:
        return None


def _firstline_doc(doc: str) -> str:
    return (doc.splitlines()[0].strip() if doc else "")


def _scan_handlers(pkg_root: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Return list of (kind, meta) for handlers under pkg_root/(transforms|transforms_domain).
    meta keys: io_type, description, inputs[], outputs[]
    """
    out: List[Tuple[str, Dict[str, Any]]] = []
    for sub in HANDLERS_SUBPKGS:
        d = pkg_root / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name == "__init__.py":
                continue
            src = _read(f)
            if not src:
                continue
            meta = _extract_meta_block(src) or {}
            try:
                tree = ast.parse(src, filename=str(f))
            except Exception:
                continue
            # discover first concrete handler class and its kind
            k = None
            desc = meta.get("description") or ""
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    base_names = {getattr(b, 'id', None) or getattr(getattr(b, 'attr', None), 'attr', None) for b in node.bases}
                    if "AbstractHandler" not in base_names:
                        continue
                    # read class doc if description missing
                    if not desc:
                        desc = _firstline_doc(ast.get_docstring(node) or "")
                    for c in node.body:
                        if isinstance(c, ast.FunctionDef) and c.name == "kind":
                            for stmt in c.body:
                                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                    k = stmt.value.value
                                    break
                    if k:
                        break
            if not k:
                # fallback: filename stem
                k = f.stem
            item = {
                "io_type": meta.get("io_type") or "",
                "description": desc or "",
                "inputs": meta.get("inputs") or [],
                "outputs": meta.get("outputs") or [],
            }
            out.append((k, item))
    return out


def list_transforms(params: dict) -> dict:
    pkg_root = Path(__file__).resolve().parent / "handlers"
    pairs = _scan_handlers(pkg_root)
    # unique by kind
    simple: List[Dict[str, Any]] = []
    seen = set()
    for kind, meta in pairs:
        if kind in seen:
            continue
        seen.add(kind)
        simple.append({
            "kind": kind,
            "io_type": meta.get("io_type", ""),
            "description": meta.get("description", ""),
            "inputs": meta.get("inputs", []),
            "outputs": meta.get("outputs", []),
        })
    simple.sort(key=lambda x: x.get("kind") or "")

    # Optional limit
    try:
        limit = int((params or {}).get("limit") or 0)
    except Exception:
        limit = 0
    out = simple[:limit] if limit and limit > 0 else simple
    return {
        "accepted": True,
        "status": "ok",
        "total": len(simple),
        "returned": len(out),
        "transforms": out,
        "truncated": bool(limit and len(simple) > len(out)),
    }
