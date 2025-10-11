"""
Chess.com API tool - Access public Chess.com data
"""
import json
import os


def spec():
    """
    Load JSON spec (source of truth)
    Returns the canonical OpenAI function schema
    """
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', '..', 'tool_specs', 'chess_com.json'))
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(operation: str, **params):
    """
    Entry point for all operations
    
    Args:
        operation: Operation to perform
        **params: Operation-specific parameters
    
    Returns:
        Dict with operation result
    """
    from .api import execute_operation
    return execute_operation(operation, **params)
