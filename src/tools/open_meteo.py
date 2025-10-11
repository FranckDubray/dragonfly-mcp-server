"""
Open-Meteo tool bootstrap
"""
import json
import os


def spec():
    """Load canonical JSON spec"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'open_meteo.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    """Execute Open-Meteo operations"""
    from ._open_meteo.api import route_operation
    return route_operation(**params)
