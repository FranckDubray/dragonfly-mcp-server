"""
API routing for device_location tool operations.
"""
from .core import get_device_location


def route_operation(operation, **kwargs):
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **kwargs: Additional operation-specific parameters
    
    Returns:
        dict: Operation result
    
    Raises:
        ValueError: If operation is unknown
    """
    if operation == 'get_location':
        provider = kwargs.get('provider', 'ipapi')
        return get_device_location(provider=provider)
    else:
        raise ValueError(f"Unknown operation: {operation}")
