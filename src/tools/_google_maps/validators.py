"""
Input validation for Google Maps operations
"""


def validate_params(params):
    """Validate and normalize parameters"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    # Validate operation-specific requirements
    if operation == 'geocode':
        if not params.get('address'):
            raise ValueError("geocode requires 'address'")
    
    elif operation in ['reverse_geocode', 'timezone', 'elevation']:
        if not (params.get('lat') is not None and params.get('lon') is not None):
            raise ValueError(f"{operation} requires 'lat' and 'lon'")
    
    elif operation == 'directions':
        if not params.get('origin'):
            raise ValueError("directions requires 'origin'")
        if not params.get('destination'):
            raise ValueError("directions requires 'destination'")
    
    elif operation == 'distance_matrix':
        if not params.get('origins'):
            raise ValueError("distance_matrix requires 'origins' array")
        if not params.get('destinations'):
            raise ValueError("distance_matrix requires 'destinations' array")
        if not isinstance(params['origins'], list):
            raise ValueError("origins must be an array")
        if not isinstance(params['destinations'], list):
            raise ValueError("destinations must be an array")
        if len(params['origins']) > 25:
            raise ValueError("origins array max length is 25")
        if len(params['destinations']) > 25:
            raise ValueError("destinations array max length is 25")
    
    elif operation == 'places_search':
        if not params.get('query'):
            raise ValueError("places_search requires 'query'")
    
    elif operation == 'place_details':
        if not params.get('place_id'):
            raise ValueError("place_details requires 'place_id'")
    
    elif operation == 'places_nearby':
        if not (params.get('lat') is not None and params.get('lon') is not None):
            raise ValueError("places_nearby requires 'lat' and 'lon'")
    
    # Validate coordinates if provided
    if 'lat' in params and params['lat'] is not None:
        lat = params['lat']
        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
            raise ValueError("lat must be a number between -90 and 90")
    
    if 'lon' in params and params['lon'] is not None:
        lon = params['lon']
        if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
            raise ValueError("lon must be a number between -180 and 180")
    
    # Set defaults
    validated = params.copy()
    validated.setdefault('mode', 'driving')
    validated.setdefault('alternatives', False)
    validated.setdefault('language', 'en')
    validated.setdefault('limit', 20)
    validated.setdefault('radius', 1000)
    
    return validated
