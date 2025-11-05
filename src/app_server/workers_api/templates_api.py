
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

async def list_templates() -> Dict[str, Any]:
    try:
        from config import find_project_root
        root = Path(find_project_root())
    except Exception:
        root = Path.cwd()
    wroot = root / 'workers'
    items: List[Dict[str, Any]] = []
    if not wroot.exists():
        return {"accepted": True, "status": "ok", "templates": []}
    for d in sorted(p for p in wroot.iterdir() if p.is_dir() and not p.name.startswith('.')):
        process_py = d / 'process.py'
        if not process_py.is_file():
            continue
        name = d.name
        title = name
        desc = ''
        has_config = (d / 'config' / 'config.json').is_file()
        has_docs = (d / 'CONFIG_DOC.json').is_file()
        if has_docs:
            try:
                doc = json.loads((d / 'CONFIG_DOC.json').read_text(encoding='utf-8'))
                title = str(doc.get('title') or title)
                desc = str(doc.get('description') or '')
            except Exception:
                pass
        items.append({
            "name": name,
            "title": title,
            "description": desc,
            "has_config": has_config,
            "has_docs": has_docs,
        })
    return {"accepted": True, "status": "ok", "templates": items}

async def get_template(name: str) -> Dict[str, Any]:
    try:
        from config import find_project_root
        root = Path(find_project_root())
    except Exception:
        root = Path.cwd()
    base = root / 'workers' / name
    if not (base / 'process.py').is_file():
        return {"accepted": False, "status": "not_found", "message": f"Template not found: {name}"}
    out: Dict[str, Any] = {"accepted": True, "status": "ok", "name": name}
    # Load config.json if present
    cfg_path = base / 'config' / 'config.json'
    if cfg_path.is_file():
        try:
            out["config"] = json.loads(cfg_path.read_text(encoding='utf-8'))
        except Exception:
            out["config_error"] = "Failed to parse config.json"
    # Load CONFIG_DOC.json if present
    doc_path = base / 'CONFIG_DOC.json'
    if doc_path.is_file():
        try:
            out["docs"] = json.loads(doc_path.read_text(encoding='utf-8'))
        except Exception:
            out["docs_error"] = "Failed to parse CONFIG_DOC.json"
    # Load optional JSON Schema for template config
    schema_path = base / 'config' / 'CONFIG_SCHEMA.json'
    if schema_path.is_file():
        try:
            out["schema"] = json.loads(schema_path.read_text(encoding='utf-8'))
        except Exception:
            out["schema_error"] = "Failed to parse CONFIG_SCHEMA.json"
    return out
