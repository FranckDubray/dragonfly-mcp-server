"""
Utility functions for ssh_admin.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """Detect project root (same strategy as sqlite3/docs)."""
    cur = Path(__file__).resolve()
    for _ in range(8):
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        if (cur / 'src').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return Path.cwd()

def resolve_local_path(local_path: str) -> Path:
    """
    Resolve local path relative to project root.
    Security: reject absolute paths and path traversal.
    """
    project_root = get_project_root()
    
    # Reject absolute paths
    if Path(local_path).is_absolute():
        raise ValueError(
            f"Absolute paths not allowed. Use relative path from project root: '{Path(local_path).name}'"
        )
    
    # Resolve relative to project root
    full_path = project_root / local_path
    
    # Security: ensure path is under project root (no traversal)
    try:
        full_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {local_path}")
    
    return full_path

def resolve_key_path(key_path: str) -> Path:
    """
    Resolve SSH key path relative to project root.
    Security: must be under ssh_keys/ directory.
    """
    project_root = get_project_root()
    
    # Reject absolute paths
    if Path(key_path).is_absolute():
        raise ValueError(
            f"Absolute paths not allowed. Use relative: 'ssh_keys/{Path(key_path).name}'"
        )
    
    # Resolve relative to project root
    full_path = project_root / key_path
    
    # Security: ensure path is under project root
    try:
        full_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {key_path}")
    
    # Check file exists
    if not full_path.exists():
        raise FileNotFoundError(
            f"SSH key not found: {key_path}\nFull path: {full_path}\n"
            f"Make sure the key exists and path is relative to project root."
        )
    
    # Warn if permissions too permissive (Unix only)
    import os
    if os.name != 'nt':  # Skip on Windows
        mode = full_path.stat().st_mode
        if mode & 0o077:
            import warnings
            warnings.warn(
                f"⚠️  SSH key {key_path} has permissive permissions. "
                f"Run: chmod 600 {full_path}"
            )
    
    return full_path

def truncate_output(text: str, max_bytes: int = 10240) -> tuple[str, bool]:
    """
    Truncate text to max_bytes with warning if truncated.
    Returns (truncated_text, was_truncated).
    """
    if len(text.encode('utf-8')) <= max_bytes:
        return text, False
    
    # Truncate to max_bytes
    truncated = text.encode('utf-8')[:max_bytes].decode('utf-8', errors='ignore')
    original_size = len(text.encode('utf-8'))
    truncated_size = len(truncated.encode('utf-8'))
    
    warning = f"\n\n[... output truncated: {original_size - truncated_size} bytes removed]"
    return truncated + warning, True
