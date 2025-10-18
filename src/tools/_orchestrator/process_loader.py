# Process loader with $import support
# Allows splitting large process files into reusable fragments

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

class ProcessLoadError(Exception):
    """Raised when process loading fails"""
    pass

def load_process_with_imports(process_file: str, base_dir: str = None) -> Dict:
    """
    Load process JSON with $import resolution.
    
    Args:
        process_file: Path to main process file (absolute or relative)
        base_dir: Base directory for resolving relative imports (default: process file's directory)
    
    Returns:
        Fully resolved process dict (all $import replaced with actual content)
    
    Raises:
        ProcessLoadError: If file not found or import fails
    
    Example:
        process = load_process_with_imports('workers/ai_curation_v6/main.process.json')
    """
    # Resolve process file path
    process_path = Path(process_file).resolve()
    if not process_path.exists():
        raise ProcessLoadError(f"Process file not found: {process_file}")
    
    # Base directory for relative imports (default: process file's directory)
    if base_dir is None:
        base_dir = process_path.parent
    else:
        base_dir = Path(base_dir).resolve()
    
    # Load main process file
    with open(process_path, 'r', encoding='utf-8') as f:
        process = json.load(f)
    
    # Resolve all $import recursively
    resolved = _resolve_imports(process, base_dir, visited=set())
    
    return resolved


def _resolve_imports(data: Any, base_dir: Path, visited: set, depth: int = 0) -> Any:
    """
    Recursively resolve $import in data structure.
    
    Args:
        data: Data structure (dict, list, or primitive)
        base_dir: Base directory for resolving relative paths
        visited: Set of visited file paths (cycle detection)
        depth: Current recursion depth (max 10)
    
    Returns:
        Resolved data with all $import replaced
    """
    # Guard: max depth to prevent infinite recursion
    if depth > 10:
        raise ProcessLoadError("Max import depth (10) exceeded - possible circular dependency")
    
    # Dict: check for $import key or recurse
    if isinstance(data, dict):
        if "$import" in data:
            return _load_import(data["$import"], base_dir, visited, depth)
        else:
            # Recurse into all dict values
            return {k: _resolve_imports(v, base_dir, visited, depth + 1) for k, v in data.items()}
    
    # List: check each item for $import or recurse
    elif isinstance(data, list):
        resolved = []
        for item in data:
            if isinstance(item, dict) and "$import" in item:
                # Import can return single item or array
                imported = _load_import(item["$import"], base_dir, visited, depth)
                if isinstance(imported, list):
                    resolved.extend(imported)  # Flatten array
                else:
                    resolved.append(imported)
            else:
                resolved.append(_resolve_imports(item, base_dir, visited, depth + 1))
        return resolved
    
    # Primitives: return as-is
    else:
        return data


def _load_import(import_path: str, base_dir: Path, visited: set, depth: int) -> Any:
    """
    Load and resolve a single $import.
    
    Args:
        import_path: Relative path to file (e.g., "prompts/sonar_fetch.json")
        base_dir: Base directory for resolving path
        visited: Set of visited files (cycle detection)
        depth: Current depth
    
    Returns:
        Loaded and resolved content
    """
    # Resolve import path (relative to base_dir)
    import_file = (base_dir / import_path).resolve()
    
    # Check if file exists
    if not import_file.exists():
        raise ProcessLoadError(f"Import file not found: {import_path} (resolved: {import_file})")
    
    # Cycle detection
    import_file_str = str(import_file)
    if import_file_str in visited:
        raise ProcessLoadError(f"Circular import detected: {import_path}")
    
    visited.add(import_file_str)
    
    # Load file
    try:
        with open(import_file, 'r', encoding='utf-8') as f:
            imported = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessLoadError(f"Invalid JSON in {import_path}: {str(e)[:200]}")
    except Exception as e:
        raise ProcessLoadError(f"Failed to load {import_path}: {str(e)[:200]}")
    
    # Recursively resolve imports in loaded content
    resolved = _resolve_imports(imported, import_file.parent, visited, depth + 1)
    
    # Remove from visited after processing (allow reuse in different branches)
    visited.discard(import_file_str)
    
    return resolved
