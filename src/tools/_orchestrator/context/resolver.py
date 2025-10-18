# Context path resolution (${worker.*}, ${cycle.*})
# Supports recursive resolution in objects and arrays (depth max 10)

import re
from typing import Any, Dict

# Pattern: ${path.to.value}
PATH_PATTERN = re.compile(r'\$\{([^}]+)\}')

class ResolutionError(Exception):
    """Raised when path resolution fails"""
    pass

def resolve_value(value: Any, worker_ctx: Dict, cycle_ctx: Dict, depth: int = 0) -> Any:
    """
    Recursively resolve ${...} references in value.
    
    Args:
        value: Input value (can be str, dict, list, primitives)
        worker_ctx: Worker context (read-only)
        cycle_ctx: Cycle context (read/write)
        depth: Current recursion depth (max 10)
    
    Returns:
        Resolved value (same type as input)
    
    Raises:
        ResolutionError: If path invalid or depth exceeded
    """
    if depth > 10:
        raise ResolutionError("Max recursion depth (10) exceeded in context resolution")
    
    # String: resolve ${...} patterns
    if isinstance(value, str):
        return _resolve_string(value, worker_ctx, cycle_ctx)
    
    # Dict: resolve all values recursively
    if isinstance(value, dict):
        return {k: resolve_value(v, worker_ctx, cycle_ctx, depth + 1) for k, v in value.items()}
    
    # List: resolve all items recursively
    if isinstance(value, list):
        return [resolve_value(item, worker_ctx, cycle_ctx, depth + 1) for item in value]
    
    # Primitives: return as-is
    return value

def _resolve_string(s: str, worker_ctx: Dict, cycle_ctx: Dict) -> Any:
    """
    Resolve ${...} in string.
    
    If string is EXACTLY "${path}", return the resolved value (any type).
    If string contains multiple ${...} or text, do string substitution.
    """
    matches = list(PATH_PATTERN.finditer(s))
    
    if not matches:
        # No ${...} → return as-is
        return s
    
    # If string is EXACTLY ${path} → return resolved value directly (any type)
    if len(matches) == 1 and matches[0].group(0) == s:
        path = matches[0].group(1)
        return _resolve_path(path, worker_ctx, cycle_ctx)
    
    # Multiple ${...} or mixed with text → string substitution
    result = s
    for match in matches:
        path = match.group(1)
        resolved = _resolve_path(path, worker_ctx, cycle_ctx)
        # Convert to string for substitution
        result = result.replace(match.group(0), str(resolved))
    
    return result

def _resolve_path(path: str, worker_ctx: Dict, cycle_ctx: Dict) -> Any:
    """
    Resolve a single path (e.g., "worker.llm_model", "cycle.ns1.uid").
    
    Args:
        path: Dotted path (e.g., "worker.llm_model")
        worker_ctx: Worker context
        cycle_ctx: Cycle context
    
    Returns:
        Resolved value
    
    Raises:
        ResolutionError: If path invalid or not found
    """
    parts = path.split('.')
    if len(parts) < 2:
        raise ResolutionError(f"Invalid path (need at least 2 parts): {path}")
    
    root = parts[0]
    rest = parts[1:]
    
    # Select context
    if root == 'worker':
        ctx = worker_ctx
    elif root == 'cycle':
        ctx = cycle_ctx
    else:
        raise ResolutionError(f"Unknown context root: {root} (expected 'worker' or 'cycle')")
    
    # Navigate path
    current = ctx
    for i, part in enumerate(rest):
        if not isinstance(current, dict):
            raise ResolutionError(f"Cannot navigate non-dict at {'.'.join(parts[:i+1])}")
        
        if part not in current:
            # Path not found → return None (or raise if strict mode)
            return None
        
        current = current[part]
    
    return current

def resolve_inputs(inputs_spec: Dict, worker_ctx: Dict, cycle_ctx: Dict) -> Dict:
    """
    Resolve all inputs for a node.
    
    Args:
        inputs_spec: Node inputs dict (may contain ${...} refs)
        worker_ctx: Worker context
        cycle_ctx: Cycle context
    
    Returns:
        Resolved inputs dict (all ${...} replaced)
    """
    return resolve_value(inputs_spec, worker_ctx, cycle_ctx)
