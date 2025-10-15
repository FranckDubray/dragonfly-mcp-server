"""
Stockfish (Auto-75) tool
"""
import json
import os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'stockfish_auto.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(operation: str, **params):
    from .api import execute_operation
    return execute_operation(operation, **params)
