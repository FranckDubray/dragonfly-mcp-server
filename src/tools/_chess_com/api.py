"""
Operation routing and orchestration
"""
from typing import Dict, Any
from . import core, validators


# All available operations
OPERATIONS = [
    'get_player_profile',
    'get_player_stats',
    'get_player_games_current',
    'get_player_games_archives_list',
    'get_player_games_archives',
    'get_player_clubs',
    'get_player_matches',
    'get_player_tournaments',
    'get_titled_players',
    'get_club_details',
    'get_club_members',
    'get_club_matches',
    'get_tournament_details',
    'get_tournament_round',
    'get_tournament_round_group',
    'get_country_details',
    'get_country_players',
    'get_country_clubs',
    'get_match_details',
    'get_match_board',
    'get_leaderboards',
    'get_daily_puzzle',
    'get_random_puzzle',
    'get_streamers',
]


def execute_operation(operation: str, **params) -> Dict[str, Any]:
    """
    Route operation to appropriate handler
    
    Args:
        operation: Operation name
        **params: Operation parameters
    
    Returns:
        Dict with operation result
    
    Raises:
        ValueError: If operation is unknown
        Exception: On API or validation errors
    """
    
    try:
        # Validate operation
        if operation not in OPERATIONS:
            return {
                'error': f"Unknown operation: {operation}",
                'available_operations': OPERATIONS,
            }
        
        # Validate params
        try:
            validated = validators.validate_params(operation, params)
        except ValueError as e:
            return {
                'error': f"Validation error: {str(e)}",
                'operation': operation,
                'params': params,
            }
        
        # Route to core logic
        handlers = {
            'get_player_profile': lambda: core.get_player_profile(**validated),
            'get_player_stats': lambda: core.get_player_stats(**validated),
            'get_player_games_current': lambda: core.get_player_games_current(**validated),
            'get_player_games_archives_list': lambda: core.get_player_games_archives_list(**validated),
            'get_player_games_archives': lambda: core.get_player_games_archives(**validated),
            'get_player_clubs': lambda: core.get_player_clubs(**validated),
            'get_player_matches': lambda: core.get_player_matches(**validated),
            'get_player_tournaments': lambda: core.get_player_tournaments(**validated),
            'get_titled_players': lambda: core.get_titled_players(**validated),
            'get_club_details': lambda: core.get_club_details(**validated),
            'get_club_members': lambda: core.get_club_members(**validated),
            'get_club_matches': lambda: core.get_club_matches(**validated),
            'get_tournament_details': lambda: core.get_tournament_details(**validated),
            'get_tournament_round': lambda: core.get_tournament_round(**validated),
            'get_tournament_round_group': lambda: core.get_tournament_round_group(**validated),
            'get_country_details': lambda: core.get_country_details(**validated),
            'get_country_players': lambda: core.get_country_players(**validated),
            'get_country_clubs': lambda: core.get_country_clubs(**validated),
            'get_match_details': lambda: core.get_match_details(**validated),
            'get_match_board': lambda: core.get_match_board(**validated),
            'get_leaderboards': lambda: core.get_leaderboards(**validated),
            'get_daily_puzzle': lambda: core.get_daily_puzzle(**validated),
            'get_random_puzzle': lambda: core.get_random_puzzle(**validated),
            'get_streamers': lambda: core.get_streamers(**validated),
        }
        
        # Execute handler
        result = handlers[operation]()
        return result
    
    except Exception as e:
        # Catch all exceptions and return structured error
        error_msg = str(e)
        
        # Extract meaningful error message
        if 'Chess.com API error' in error_msg:
            # Already formatted error from chess_client
            return {
                'error': error_msg,
                'operation': operation,
            }
        elif 'Resource not found' in error_msg or '404' in error_msg:
            return {
                'error': f"Resource not found. The requested {operation.replace('get_', '').replace('_', ' ')} does not exist on Chess.com.",
                'operation': operation,
                'params': params,
            }
        elif 'Rate limit' in error_msg or '429' in error_msg:
            return {
                'error': "Rate limit exceeded. Please wait a moment and try again.",
                'operation': operation,
            }
        else:
            # Generic error
            return {
                'error': f"Error executing {operation}: {error_msg}",
                'operation': operation,
            }
