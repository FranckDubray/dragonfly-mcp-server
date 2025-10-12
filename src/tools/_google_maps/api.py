"""
Google Maps API routing
"""
from .validators import validate_params
from .operations_geo import (
    geocode_address,
    reverse_geocode_coords,
    get_timezone,
    get_elevation
)
from .core import (
    get_directions,
    get_distance_matrix
)
from .operations_places import (
    search_places,
    get_place_details,
    search_nearby_places
)


def route_operation(**params):
    """Route to appropriate handler based on operation"""
    try:
        # Validate and normalize params
        validated = validate_params(params)
        operation = validated['operation']
        
        # Route to handlers
        if operation == 'geocode':
            return geocode_address(validated)
        elif operation == 'reverse_geocode':
            return reverse_geocode_coords(validated)
        elif operation == 'directions':
            return get_directions(validated)
        elif operation == 'distance_matrix':
            return get_distance_matrix(validated)
        elif operation == 'places_search':
            return search_places(validated)
        elif operation == 'place_details':
            return get_place_details(validated)
        elif operation == 'places_nearby':
            return search_nearby_places(validated)
        elif operation == 'timezone':
            return get_timezone(validated)
        elif operation == 'elevation':
            return get_elevation(validated)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }
