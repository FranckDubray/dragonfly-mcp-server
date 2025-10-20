# Process loader - $import resolution (<5KB)

import json
import re
from pathlib import Path
from typing import Any, Dict, List

# Pattern: ${path.to.value}
PATH_PATTERN = re.compile(r'\$\{([^}]+)\}')

class ProcessLoadError(Exception):
    """Raised when process loading fails"""
    pass


def _candidate_import_paths(base_dir: Path, import_path: str) -> List[Path]:
    """Return candidate absolute paths for an import, in priority order."""
    paths: List[Path] = []
    p1 = (base_dir / import_path).resolve()
    paths.append(p1)
    p2 = (base_dir / 'nodes' / import_path).resolve()
    if p2 not in paths:
        paths.append(p2)
    return paths


def _load_import(import_path: str, base_dir: Path, visited: set, depth: int) -> Any:
    """
    Load and resolve a single $import.
    
    Args:
        import_path: Relative path to file
        base_dir: Base directory for resolving path
        visited: Set of visited files (cycle detection)
        depth: Current depth
    
    Returns:
        Loaded and resolved content
    """
    last_err = None
    candidates = _candidate_import_paths(base_dir, import_path)
    candidates_str = "\n  - ".join(str(p) for p in candidates)

    for candidate in candidates:
        try:
            if not candidate.exists():
                continue
            
            # Cycle detection
            candidate_str = str(candidate)
            if candidate_str in visited:
                raise ProcessLoadError(
                    f"Circular import detected!\n"
                    f"Import path: {import_path}\n"
                    f"File already visited: {candidate}\n"
                    f"Import chain: {' -> '.join(sorted(visited))}\n"
                    f"Check for circular dependencies in your $import declarations."
                )
            visited.add(candidate_str)
            
            # Load file
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
            except json.JSONDecodeError as e:
                raise ProcessLoadError(
                    f"Invalid JSON in imported file: {import_path}\n"
                    f"Resolved to: {candidate}\n"
                    f"Error at line {e.lineno}, column {e.colno}: {e.msg}\n"
                    f"Check JSON syntax (trailing commas, quotes, brackets)."
                )
            except Exception as e:
                raise ProcessLoadError(
                    f"Failed to read imported file: {import_path}\n"
                    f"Resolved to: {candidate}\n"
                    f"Error: {str(e)}"
                )
            
            # Recursively resolve imports in loaded content
            resolved = resolve_imports_recursive(imported, candidate.parent, visited, depth + 1)
            
            # Remove from visited after processing
            visited.discard(candidate_str)
            return resolved
        
        except ProcessLoadError as e:
            last_err = e
            break
        except Exception as e:
            last_err = ProcessLoadError(
                f"Unexpected error loading import: {import_path}\n"
                f"Tried: {candidate}\n"
                f"Error: {str(e)}"
            )
            break

    if last_err is not None:
        raise last_err
    
    raise ProcessLoadError(
        f"Import file not found: {import_path}\n"
        f"Searched in:\n  - {candidates_str}\n"
        f"Base directory: {base_dir}\n\n"
        f"Tip: Imported files can be placed in:\n"
        f"  1. Same directory as process file\n"
        f"  2. 'nodes/' subdirectory (recommended for organization)\n\n"
        f"Check:\n"
        f"  - File name spelling and extension (.json)\n"
        f"  - Relative path from {base_dir}\n"
        f"  - File permissions (readable)"
    )


def resolve_imports_recursive(data: Any, base_dir: Path, visited: set, depth: int = 0) -> Any:
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
    if depth > 10:
        raise ProcessLoadError(
            f"Max import depth (10) exceeded - possible circular dependency.\n"
            f"Import chain is too deep. Check for circular imports or excessive nesting.\n"
            f"Current base directory: {base_dir}"
        )
    
    # Dict: check for $import key or recurse
    if isinstance(data, dict):
        if "$import" in data:
            return _load_import(data["$import"], base_dir, visited, depth)
        else:
            return {k: resolve_imports_recursive(v, base_dir, visited, depth + 1) for k, v in data.items()}
    
    # List: check each item for $import or recurse
    elif isinstance(data, list):
        resolved = []
        for item in data:
            if isinstance(item, dict) and "$import" in item:
                imported = _load_import(item["$import"], base_dir, visited, depth)
                if isinstance(imported, list):
                    resolved.extend(imported)
                else:
                    resolved.append(imported)
            else:
                resolved.append(resolve_imports_recursive(item, base_dir, visited, depth + 1))
        return resolved
    
    # Primitives: return as-is
    else:
        return data
