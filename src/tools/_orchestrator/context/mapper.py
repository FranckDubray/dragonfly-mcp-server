# Context output mapping (handler outputs → cycle_ctx)
# Enforces write restrictions (only cycle.* paths allowed)

from typing import Any, Dict

class MappingError(Exception):
    """Raised when output mapping fails"""
    pass

def assign_outputs(cycle_ctx: Dict, outputs_data: Dict, outputs_spec: Dict) -> None:
    """
    Map handler outputs to cycle_ctx paths.
    
    Args:
        cycle_ctx: Cycle context (modified in-place)
        outputs_data: Handler outputs (flat dict)
        outputs_spec: Node outputs spec (output_key → cycle.path)
    
    Raises:
        MappingError: If path invalid or write forbidden
    
    Example:
        outputs_data = {"san_text": "hello", "truncated": False}
        outputs_spec = {
            "san_text": "cycle.ns1.san_text",
            "truncated": "cycle.ns1.truncated"
        }
        → cycle_ctx["ns1"]["san_text"] = "hello", cycle_ctx["ns1"]["truncated"] = False
    """
    for output_key, path in outputs_spec.items():
        if output_key not in outputs_data:
            # Output key not returned by handler → skip (optional output)
            continue
        
        value = outputs_data[output_key]
        _assign_path(cycle_ctx, path, value)

def _assign_path(cycle_ctx: Dict, path: str, value: Any) -> None:
    """
    Assign value to a path in cycle_ctx.
    
    Args:
        cycle_ctx: Cycle context (modified in-place)
        path: Dotted path (must start with "cycle.")
        value: Value to assign
    
    Raises:
        MappingError: If path invalid or write forbidden
    """
    if not path.startswith('cycle.'):
        raise MappingError(f"Write forbidden: path must start with 'cycle.' (got: {path})")
    
    parts = path.split('.')[1:]  # Remove 'cycle' prefix
    if len(parts) < 1:
        raise MappingError(f"Invalid path (need at least cycle.namespace): {path}")
    
    # Navigate to parent, create intermediate dicts if needed
    current = cycle_ctx
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            raise MappingError(f"Cannot navigate non-dict at {path}")
        current = current[part]
    
    # Assign final value
    final_key = parts[-1]
    current[final_key] = value

def reset_scope(cycle_ctx: Dict, scope_name: str) -> None:
    """
    Reset (clear) a scope in cycle_ctx.
    
    Args:
        cycle_ctx: Cycle context (modified in-place)
        scope_name: Scope name (e.g., "ns1")
    """
    if scope_name in cycle_ctx:
        del cycle_ctx[scope_name]

def seed_scope(cycle_ctx: Dict, scope_name: str, seed_data: Dict) -> None:
    """
    Seed a scope with initial data (after reset).
    
    Args:
        cycle_ctx: Cycle context (modified in-place)
        scope_name: Scope name (e.g., "ns1")
        seed_Initial data (flat dict)
    """
    if scope_name not in cycle_ctx:
        cycle_ctx[scope_name] = {}
    
    cycle_ctx[scope_name].update(seed_data)
