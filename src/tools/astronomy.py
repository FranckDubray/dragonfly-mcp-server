"""
Astronomy & Space tool
Complete astronomy calculations using Skyfield (100% local, no API required)
"""

import json
import os


def spec():
    """Load canonical spec from JSON"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'astronomy.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    """Execute astronomy operation"""
    from ._astronomy.api import route_operation
    return route_operation(params)
