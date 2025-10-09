"""API routing for ship tracker operations."""

from typing import Dict, Any
from .core import handle_track_ships, handle_get_ship_details, handle_get_port_traffic


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    handlers = {
        "track_ships": handle_track_ships,
        "get_ship_details": handle_get_ship_details,
        "get_port_traffic": handle_get_port_traffic
    }
    
    handler = handlers.get(operation)
    if not handler:
        return {
            "error": f"Unknown operation: {operation}",
            "available_operations": list(handlers.keys())
        }
    
    return handler(**params)
