"""Chroot and path utilities for Git tool.
All filesystem access must go through these helpers to enforce project-root chroot.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from config import find_project_root
except ImportError:
    # Fallback during isolated runs/tests
    find_project_root = lambda: Path.cwd()


def chroot_base() -> Path:
    return find_project_root().resolve()


def resolve_in_chroot(rel_path: Optional[str]) -> Path:
    base = chroot_base()
    if not rel_path or str(rel_path).strip() in ("", ".", "/"):
        return base
    p = (base / rel_path).resolve()
    if not str(p).startswith(str(base)):
        raise ValueError(f"Path escapes chroot: {rel_path}")
    return p


def read_file_in_chroot(local_path: str) -> str:
    p = resolve_in_chroot(local_path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {local_path}")
    return p.read_text(encoding="utf-8")


def sanitize_repo_dir(param_repo_dir: Optional[str]) -> Path:
    try:
        return resolve_in_chroot(param_repo_dir)
    except Exception:
        return chroot_base()


def sanitize_paths_within_repo(repo_dir: Path, paths: List[str]) -> List[str]:
    clean: List[str] = []
    for p in paths:
        rp = (repo_dir / p).resolve()
        if not str(rp).startswith(str(repo_dir)):
            continue
        clean.append(str(rp.relative_to(repo_dir)))
    return clean
