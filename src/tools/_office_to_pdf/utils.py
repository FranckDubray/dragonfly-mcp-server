"""Utility functions for office_to_pdf."""

from pathlib import Path
from typing import Dict, Any


def get_project_root() -> Path:
    """Get project root directory."""
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        cur = cur.parent
    return Path.cwd()


def get_unique_output_path(output_path: str, overwrite: bool = False) -> str:
    """Get unique output path (add suffixes if file exists).
    
    Args:
        output_path: Desired output path
        overwrite: If True, return as-is. If False, add suffix if exists.
        
    Returns:
        Unique output path
    """
    if overwrite:
        return output_path
    
    project_root = get_project_root()
    abs_output_path = project_root / output_path
    
    if not abs_output_path.exists():
        return output_path
    
    # File exists, add suffix
    base = abs_output_path.stem  # filename without extension
    parent = abs_output_path.parent
    ext = abs_output_path.suffix
    
    counter = 1
    while True:
        new_name = f"{base}_{counter}{ext}"
        new_path = parent / new_name
        if not new_path.exists():
            # Return relative path
            return str(new_path.relative_to(project_root))
        counter += 1


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get file metadata.
    
    Args:
        file_path: Path to file (relative to project root)
        
    Returns:
        File metadata dict
    """
    project_root = get_project_root()
    abs_path = project_root / file_path
    
    stat = abs_path.stat()
    
    # Determine file type
    ext = abs_path.suffix.lower()
    if ext in [".docx", ".doc"]:
        file_type = "Word document"
        app_type = "Microsoft Word"
    elif ext in [".pptx", ".ppt"]:
        file_type = "PowerPoint presentation"
        app_type = "Microsoft PowerPoint"
    else:
        file_type = "Unknown"
        app_type = "Unknown"
    
    return {
        "path": file_path,
        "name": abs_path.name,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "extension": ext,
        "file_type": file_type,
        "app_type": app_type,
        "exists": True
    }
