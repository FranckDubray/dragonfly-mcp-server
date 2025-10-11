"""
OpenWeatherMap tool bootstrap
"""
import json
import os


def spec():
    """Load canonical JSON spec"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'openweathermap.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    """Execute OpenWeatherMap operations"""
    from ._openweathermap.api import route_operation
    return route_operation(**params)
