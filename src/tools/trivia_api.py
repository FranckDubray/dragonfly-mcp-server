"""
Trivia API tool - Open Trivia Database client
Bootstrap file (no underscore prefix)
"""
import json
import os


def spec():
    """Load canonical JSON spec"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'trivia_api.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(**params):
    """Execute trivia_api operation"""
    from ._trivia_api.api import route_operation
    return route_operation(params)
