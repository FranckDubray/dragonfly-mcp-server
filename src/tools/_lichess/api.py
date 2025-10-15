"""
Operation routing and orchestration for Lichess tool (public endpoints only)
"""
from typing import Dict, Any
from . import core, validators

OPERATIONS = [
    'get_user_profile',
    'get_user_perfs',
    'get_user_teams',
    'get_user_current_game',
    'get_user_games',
    'get_team_details',
    'get_team_members',
    'get_tournament_details',
    'get_tournament_results',
    'get_top_players',
    'get_daily_puzzle',
    'get_puzzle',
]


def execute_operation(operation: str, **params) -> Dict[str, Any]:
    try:
        if operation not in OPERATIONS:
            return {
                'error': f"Unknown operation: {operation}",
                'available_operations': OPERATIONS,
            }
        try:
            validated = validators.validate_params(operation, params)
        except ValueError as e:
            return {
                'error': f"Validation error: {str(e)}",
                'operation': operation,
                'params': params,
            }

        handlers = {
            'get_user_profile': lambda: core.get_user_profile(**validated),
            'get_user_perfs': lambda: core.get_user_perfs(**validated),
            'get_user_teams': lambda: core.get_user_teams(**validated),
            'get_user_current_game': lambda: core.get_user_current_game(**validated),
            'get_user_games': lambda: core.get_user_games(**validated),
            'get_team_details': lambda: core.get_team_details(**validated),
            'get_team_members': lambda: core.get_team_members(**validated),
            'get_tournament_details': lambda: core.get_tournament_details(**validated),
            'get_tournament_results': lambda: core.get_tournament_results(**validated),
            'get_top_players': lambda: core.get_top_players(**validated),
            'get_daily_puzzle': lambda: core.get_daily_puzzle(**validated),
            'get_puzzle': lambda: core.get_puzzle(**validated),
        }
        return handlers[operation]()
    except Exception as e:
        msg = str(e)
        if '404' in msg or 'not found' in msg.lower():
            return {'error': 'Resource not found on Lichess.', 'operation': operation, 'params': params}
        if '429' in msg or 'rate limit' in msg.lower():
            return {'error': 'Rate limit exceeded on Lichess. Please slow down.', 'operation': operation}
        return {'error': f"Error executing {operation}: {msg}", 'operation': operation}
