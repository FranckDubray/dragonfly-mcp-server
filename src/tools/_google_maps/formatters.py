"""
Formatting utilities for Google Maps responses
"""


def format_location(data):
    """Format geocoding result"""
    geometry = data.get('geometry', {})
    location = geometry.get('location', {})
    
    return {
        'formatted_address': data.get('formatted_address'),
        'place_id': data.get('place_id'),
        'types': data.get('types', []),
        'coordinates': {
            'lat': location.get('lat'),
            'lon': location.get('lng')
        },
        'location_type': geometry.get('location_type'),
        'viewport': {
            'northeast': {
                'lat': geometry.get('viewport', {}).get('northeast', {}).get('lat'),
                'lon': geometry.get('viewport', {}).get('northeast', {}).get('lng')
            },
            'southwest': {
                'lat': geometry.get('viewport', {}).get('southwest', {}).get('lat'),
                'lon': geometry.get('viewport', {}).get('southwest', {}).get('lng')
            }
        } if 'viewport' in geometry else None,
        'address_components': [
            {
                'long_name': comp.get('long_name'),
                'short_name': comp.get('short_name'),
                'types': comp.get('types', [])
            }
            for comp in data.get('address_components', [])
        ]
    }


def format_route(data):
    """Format directions route"""
    legs = data.get('legs', [])
    
    return {
        'summary': data.get('summary'),
        'copyrights': data.get('copyrights'),
        'warnings': data.get('warnings', []),
        'waypoint_order': data.get('waypoint_order', []),
        'bounds': {
            'northeast': {
                'lat': data.get('bounds', {}).get('northeast', {}).get('lat'),
                'lon': data.get('bounds', {}).get('northeast', {}).get('lng')
            },
            'southwest': {
                'lat': data.get('bounds', {}).get('southwest', {}).get('lat'),
                'lon': data.get('bounds', {}).get('southwest', {}).get('lng')
            }
        } if 'bounds' in data else None,
        'overview_polyline': data.get('overview_polyline', {}).get('points'),
        'legs': [
            {
                'start_address': leg.get('start_address'),
                'end_address': leg.get('end_address'),
                'start_location': {
                    'lat': leg.get('start_location', {}).get('lat'),
                    'lon': leg.get('start_location', {}).get('lng')
                },
                'end_location': {
                    'lat': leg.get('end_location', {}).get('lat'),
                    'lon': leg.get('end_location', {}).get('lng')
                },
                'distance': {
                    'meters': leg.get('distance', {}).get('value'),
                    'text': leg.get('distance', {}).get('text')
                },
                'duration': {
                    'seconds': leg.get('duration', {}).get('value'),
                    'text': leg.get('duration', {}).get('text')
                },
                'duration_in_traffic': {
                    'seconds': leg.get('duration_in_traffic', {}).get('value'),
                    'text': leg.get('duration_in_traffic', {}).get('text')
                } if 'duration_in_traffic' in leg else None,
                'steps': [
                    {
                        'travel_mode': step.get('travel_mode'),
                        'start_location': {
                            'lat': step.get('start_location', {}).get('lat'),
                            'lon': step.get('start_location', {}).get('lng')
                        },
                        'end_location': {
                            'lat': step.get('end_location', {}).get('lat'),
                            'lon': step.get('end_location', {}).get('lng')
                        },
                        'distance': {
                            'meters': step.get('distance', {}).get('value'),
                            'text': step.get('distance', {}).get('text')
                        },
                        'duration': {
                            'seconds': step.get('duration', {}).get('value'),
                            'text': step.get('duration', {}).get('text')
                        },
                        'html_instructions': step.get('html_instructions'),
                        'polyline': step.get('polyline', {}).get('points')
                    }
                    for step in leg.get('steps', [])
                ]
            }
            for leg in legs
        ]
    }


def format_place(data, detailed=False):
    """Format place result"""
    geometry = data.get('geometry', {})
    location = geometry.get('location', {})
    
    formatted = {
        'name': data.get('name'),
        'place_id': data.get('place_id'),
        'formatted_address': data.get('formatted_address') or data.get('vicinity'),
        'coordinates': {
            'lat': location.get('lat'),
            'lon': location.get('lng')
        },
        'types': data.get('types', []),
        'rating': data.get('rating'),
        'user_ratings_total': data.get('user_ratings_total'),
        'price_level': data.get('price_level')
    }
    
    # Add detailed fields if requested
    if detailed:
        formatted['formatted_phone_number'] = data.get('formatted_phone_number')
        formatted['international_phone_number'] = data.get('international_phone_number')
        formatted['website'] = data.get('website')
        formatted['opening_hours'] = {
            'open_now': data.get('opening_hours', {}).get('open_now'),
            'weekday_text': data.get('opening_hours', {}).get('weekday_text', [])
        } if 'opening_hours' in data else None
        formatted['photos'] = [
            {
                'photo_reference': photo.get('photo_reference'),
                'width': photo.get('width'),
                'height': photo.get('height')
            }
            for photo in data.get('photos', [])[:5]  # Limit to 5 photos
        ] if 'photos' in data else []
    else:
        formatted['opening_hours_open_now'] = data.get('opening_hours', {}).get('open_now')
    
    return formatted
