"""
Device Location Tool - Bootstrap module.
Get GPS coordinates and location information for the current device.
"""
from _device_location import spec as get_spec
from _device_location.api import route_operation


def spec():
    """Return tool specification (loaded from JSON)."""
    return get_spec()


def run(**params):
    """
    Execute device location operation.
    
    Args:
        operation: Operation to perform ('get_location')
        provider: Geolocation provider ('ipapi' or 'ip-api', default: 'ipapi')
    
    Returns:
        dict: Location information with GPS coordinates and metadata
    
    Raises:
        ValueError: If operation is invalid
        Exception: If geolocation request fails
    """
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    return route_operation(**params)
