"""
API routing for device_location tool operations.
"""
import logging
from .core import get_device_location
from .validators import validate_operation, validate_provider

LOG = logging.getLogger(__name__)


def route_operation(operation, **kwargs):
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **kwargs: Additional operation-specific parameters
    
    Returns:
        dict: Operation result
    
    Raises:
        ValueError: If operation is unknown or params invalid
    """
    try:
        operation = validate_operation(operation)
        if operation == 'get_location':
            provider = validate_provider(kwargs.get('provider'))
            return get_device_location(provider=provider)
        # Should not reach due to validator, keep guard
        raise ValueError(f"Unknown operation: {operation}")
    except Exception as e:
        LOG.error(f"device_location operation failed: {e}")
        # Re-raise to bubble up minimal error (no verbose metadata in output)
        raise
