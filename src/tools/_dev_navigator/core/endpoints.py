from typing import Any, Dict, List
import os

from ..services.pagination import paginate_list
from ..services.pathing import resolve_root_and_abs
from ..services.fs_scanner import iter_files, read_text_head
from ..services.globber import allowed_by_globs
from ..services.budget_broker import compute_effective_budgets
from ..connectors.python.endpoints_fastapi import extract_endpoints as fe_fastapi
from ..connectors.python.endpoints_flask import extract_endpoints as fe_flask
from ..connectors.python.endpoints_django import extract_endpoints as fe_django
from ..connectors.javascript.endpoints_express import extract_endpoints_express as fe_express
from ..connectors.php.endpoints_symfony import extract_endpoints_symfony as fe_symfony
from ..services.yaml_router_extractors import extract_yaml_gateway, find_yaml_includes


def _resolve_and_read(root: str, base_rel: str, inc: str, max_bytes: int) -> List[Dict[str, Any]]:
    """Resolve YAML include path relative to base_rel directory and return [(rel, text)] best-effort.
    Supports directories (will scan *.yaml/*.yml under it) and files.
    """
    out: List[Dict[str, Any]] = []
    base_dir = os.path.dirname(base_rel)
    candidate = os.path.normpath(os.path.join(base_dir, inc))
    abs_candidate = os.path.abspath(os.path.join(root, candidate))
    if not abs_candidate.startswith(os.path.abspath(root)):
        return out
    if os.path.isdir(abs_candidate):
        # list yaml files
        for name in os.listdir(abs_candidate):
            if name.endswith(('.yaml','.yml')):
                rel = os.path.relpath(os.path.join(abs_candidate, name), root)
                try:
                    with open(os.path.join(root, rel), 'rb') as f:
                        text = f.read(max_bytes).decode('utf-8', errors='replace')
                    out.append({'rel': rel, 'text': text})
                except Exception:
                    continue
    else:
        if not candidate.endswith(('.yaml','.yml')):
            # try adding .yaml
            for ext in ('.yaml','.yml'):
                alt = candidate + ext
                abs_alt = os.path.abspath(os.path.join(root, alt))
                if os.path.isfile(abs_alt):
                    candidate = alt
                    abs_candidate = abs_alt
                    break
        if os.path.isfile(abs_candidate):
            rel = os.path.relpath(abs_candidate, root)
            try:
                with open(abs_candidate, 'rb') as f:
                    text = f.read(max_bytes).decode('utf-8', errors='replace')
                out.append({'rel': rel, 'text': text})
            except Exception:
                pass
    return out


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    includes = p.get("glob_include") or []
    excludes = p.get("glob_exclude") or []

    eff = compute_effective_budgets(p)
    limit = eff["limit"]

    root = p["path"]
    scope_path = p.get("scope_path")

    items: List[Dict[str, Any]] = []
    scanned = 0
    for rel, _size in iter_files(root, scope_path, eff["max_files_scanned"]):
        if not allowed_by_globs(rel, includes, excludes):
            continue
        base, abs_path = resolve_root_and_abs(root, rel)
        text = read_text_head(abs_path, eff["max_bytes_per_file"])
        # Aggregate endpoints from multiple paradigms
        if rel.endswith('.py'):
            items.extend(fe_fastapi(text, rel))
            items.extend(fe_flask(text, rel))
            if os.path.basename(rel) == 'urls.py':
                items.extend(fe_django(text, rel))
        if rel.endswith(('.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx')):
            items.extend(fe_express(text, rel))
        if rel.endswith(('.php',)):
            items.extend(fe_symfony(text, rel))
        if rel.endswith(('.yaml', '.yml')):
            # Try Symfony-style first (attributes-like YAML), then generic gateway
            eps = fe_symfony(text, rel)
            if not eps:
                eps = extract_yaml_gateway(text, rel)
            items.extend(eps)
            # Follow includes/imports/resources best-effort
            for inc in find_yaml_includes(text):
                for sub in _resolve_and_read(root, rel, inc, eff["max_bytes_per_file"]):
                    sub_eps = fe_symfony(sub['text'], sub['rel'])
                    if not sub_eps:
                        sub_eps = extract_yaml_gateway(sub['text'], sub['rel'])
                    items.extend(sub_eps)
        scanned += 1
        if len(items) >= limit * 2:
            break

    items.sort(key=lambda x: (x.get("path_or_name",""), x.get("method","")))

    page, total, next_c = paginate_list(items, limit, p.get("cursor"))
    return {
        "operation": "endpoints",
        "data": page,
        "returned_count": len(page),
        "total_count": total,
        "truncated": next_c is not None,
        "next_cursor": next_c,
        "stats": {"scanned_files": scanned}
    }
