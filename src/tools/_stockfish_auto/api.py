"""
Routing for Stockfish Auto-75
"""
from typing import Dict, Any
from . import core, validators

OPERATIONS = ['evaluate_position', 'analyze_game']


def execute_operation(operation: str, **params) -> Dict[str, Any]:
    try:
        if operation not in OPERATIONS:
            return {'error': f'Unknown operation: {operation}', 'available_operations': OPERATIONS}
        try:
            validated = validators.validate_params(operation, params)
        except ValueError as e:
            return {'error': f'Validation error: {str(e)}', 'operation': operation, 'params': params}
        handlers = {
            'evaluate_position': lambda: core.evaluate_position(**validated),
            'analyze_game': lambda: core.analyze_game(**validated),
        }
        return handlers[operation]()
    except Exception as e:
        return {'error': f'Error executing {operation}: {str(e)}', 'operation': operation}
