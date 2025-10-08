"""
Lightweight storage helpers for script_executor tool.
- Scripts are stored under <project_root>/script_executor
- File names are sanitized to avoid traversal; default extension: .py
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

# Compute project root: .../src/tools/_script_executor/storage.py -> project_root = parents[3]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = _PROJECT_ROOT / "script_executor"
_ALLOWED_NAME = re.compile(r"^[A-Za-z0-9._\-]+$")


def scripts_dir() -> Path:
    _SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    return _SCRIPTS_DIR


def sanitize_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Empty script name")
    # enforce simple names (prevent traversal)
    base = name.split("/")[-1].split("\\")[-1]
    if not _ALLOWED_NAME.match(base):
        raise ValueError("Invalid script name: only letters, digits, dot, underscore and hyphen are allowed")
    if "." not in base:
        base += ".py"
    return base


def resolve_path(name: str) -> Path:
    base = sanitize_name(name)
    p = scripts_dir() / base
    # Ensure the path stays under scripts_dir
    if scripts_dir() not in p.resolve().parents and p.resolve() != scripts_dir():
        raise ValueError("Refused path outside scripts directory")
    return p


def save_script(name: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    p = resolve_path(name)
    if p.exists() and not overwrite:
        return {
            "success": False,
            "error": "File already exists. Use overwrite=true to replace.",
            "path": str(p),
            "name": p.name,
        }
    data = content if isinstance(content, str) else str(content)
    scripts_dir().mkdir(parents=True, exist_ok=True)
    p.write_text(data, encoding="utf-8")
    return {
        "success": True,
        "path": str(p),
        "name": p.name,
        "size_bytes": p.stat().st_size,
    }


def load_script(name: str) -> Dict[str, Any]:
    p = resolve_path(name)
    if not p.exists():
        return {"success": False, "error": "Script not found", "name": p.name, "path": str(p)}
    content = p.read_text(encoding="utf-8")
    return {"success": True, "name": p.name, "path": str(p), "content": content}


def list_scripts() -> Dict[str, Any]:
    d = scripts_dir()
    entries: List[Dict[str, Any]] = []
    if d.exists():
        for f in sorted(d.glob("*.py")):
            try:
                st = f.stat()
                entries.append({
                    "name": f.name,
                    "path": str(f),
                    "size_bytes": st.st_size,
                })
            except Exception:
                continue
    return {"success": True, "count": len(entries), "scripts": entries}
