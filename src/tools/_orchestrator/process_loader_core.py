# Process loader core - Main entry point (<4KB)

import json
from pathlib import Path
from typing import Any, Dict
from .process_loader_imports import resolve_imports_recursive, ProcessLoadError
from .process_loader_subgraphs import flatten_subgraphs


def load_process_with_imports(process_file: str, base_dir: str = None) -> Dict:
    """
    Load process JSON with $import resolution + subgraph flattening.
    
    Args:
        process_file: Path to main process file (absolute or relative)
        base_dir: Base directory for resolving relative imports (default: process file's directory)
    
    Returns:
        Fully resolved process dict (all $import replaced + subgraphs flattened)
    
    Raises:
        ProcessLoadError: If file not found or import fails
    
    Example:
        process = load_process_with_imports('workers/ai_curation/main.process.json')
    """
    # Resolve process file path
    process_path = Path(process_file).resolve()
    if not process_path.exists():
        raise ProcessLoadError(
            f"Process file not found: {process_file}\n"
            f"Resolved path: {process_path}\n"
            f"Check that the file exists and path is correct."
        )
    
    # Base directory for relative imports (default: process file's directory)
    if base_dir is None:
        base_dir = process_path.parent
    else:
        base_dir = Path(base_dir).resolve()
    
    # Load main process file
    try:
        with open(process_path, 'r', encoding='utf-8') as f:
            process = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessLoadError(
            f"Invalid JSON in process file: {process_file}\n"
            f"Error at line {e.lineno}, column {e.colno}: {e.msg}\n"
            f"Check JSON syntax (trailing commas, quotes, brackets)."
        )
    except Exception as e:
        raise ProcessLoadError(
            f"Failed to read process file: {process_file}\n"
            f"Error: {str(e)}"
        )
    
    # Resolve all $import recursively
    try:
        resolved = resolve_imports_recursive(process, base_dir, visited=set())
    except ProcessLoadError:
        raise  # Re-raise with original context
    except Exception as e:
        raise ProcessLoadError(
            f"Unexpected error resolving imports in: {process_file}\n"
            f"Error: {str(e)}"
        )
    
    # Flatten subgraphs if present
    if 'graph' in resolved and 'subgraphs' in resolved.get('graph', {}):
        resolved = flatten_subgraphs(resolved, base_dir)
    
    return resolved
