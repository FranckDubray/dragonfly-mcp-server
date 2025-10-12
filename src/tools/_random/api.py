"""API routing for random operations."""

from typing import Dict, Any
from .core import (
    handle_generate_integers,
    handle_generate_floats,
    handle_generate_bytes,
    handle_coin_flip,
    handle_dice_roll,
    handle_shuffle,
    handle_pick_random
)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    handlers = {
        "generate_integers": handle_generate_integers,
        "generate_floats": handle_generate_floats,
        "generate_bytes": handle_generate_bytes,
        "coin_flip": handle_coin_flip,
        "dice_roll": handle_dice_roll,
        "shuffle": handle_shuffle,
        "pick_random": handle_pick_random
    }
    
    handler = handlers.get(operation)
    if not handler:
        return {
            "error": f"Unknown operation: {operation}",
            "available_operations": list(handlers.keys())
        }
    
    try:
        return handler(**params)
    except Exception as e:
        return {
            "error": f"Operation {operation} failed: {str(e)}",
            "operation": operation
        }
