"""
Input validation and normalization
"""
import re
from datetime import datetime
from typing import Dict, Any, List


def validate_params(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize parameters based on operation"""
    
    validators_map = {
        'get_player_profile': validate_player_profile,
        'get_player_stats': validate_player_stats,
        'get_player_games_current': validate_player_games_current,
        'get_player_games_archives_list': validate_player_games_archives_list,
        'get_player_games_archives': validate_player_games_archives,
        'get_player_clubs': validate_player_clubs,
        'get_player_matches': validate_player_matches,
        'get_player_tournaments': validate_player_tournaments,
        'get_titled_players': validate_titled_players,
        'get_club_details': validate_club_details,
        'get_club_members': validate_club_members,
        'get_club_matches': validate_club_matches,
        'get_tournament_details': validate_tournament_details,
        'get_tournament_round': validate_tournament_round,
        'get_tournament_round_group': validate_tournament_round_group,
        'get_country_details': validate_country_details,
        'get_country_players': validate_country_players,
        'get_country_clubs': validate_country_clubs,
        'get_match_details': validate_match_details,
        'get_match_board': validate_match_board,
        'get_leaderboards': validate_leaderboards,
        'get_daily_puzzle': validate_daily_puzzle,
        'get_random_puzzle': validate_random_puzzle,
        'get_streamers': validate_streamers,
    }
    
    if operation in validators_map:
        return validators_map[operation](params)
    
    return params


def validate_limit(limit: Any, default: int = 50, maximum: int = 500) -> int:
    """
    Validate and normalize limit parameter
    Default: 50, Min: 1, Max: 500 (or custom maximum)
    """
    if limit is None:
        return default
    
    if not isinstance(limit, int):
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            return default
    
    if limit < 1:
        return 1
    if limit > maximum:
        return maximum
    
    return limit


def validate_categories(categories: Any) -> List[str]:
    """
    Validate leaderboard categories
    """
    valid_categories = [
        'daily', 'daily960', 'live_rapid', 'live_blitz', 'live_bullet',
        'live_bughouse', 'live_blitz960', 'live_threecheck', 'live_crazyhouse', 'live_kingofthehill'
    ]
    
    if categories is None or categories == []:
        return valid_categories  # Return all if not specified
    
    if not isinstance(categories, list):
        raise ValueError(f"categories must be a list, got: {type(categories).__name__}")
    
    validated = []
    for cat in categories:
        if not isinstance(cat, str):
            raise ValueError(f"Each category must be a string, got: {type(cat).__name__}")
        
        cat = cat.strip().lower()
        if cat not in valid_categories:
            raise ValueError(f"Invalid category: {cat}. Valid categories: {', '.join(valid_categories)}")
        
        if cat not in validated:
            validated.append(cat)
    
    if not validated:
        return valid_categories
    
    return validated


def validate_username(username: str) -> str:
    """Validate and normalize Chess.com username"""
    if not username or not username.strip():
        raise ValueError("username is required")
    
    username = username.strip().lower()
    
    # Chess.com allows letters, numbers, _, -, .
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        raise ValueError(f"Invalid username format: {username}")
    
    if len(username) < 2 or len(username) > 25:
        raise ValueError(f"Username must be 2-25 characters: {username}")
    
    return username


def validate_club_id(club_id: str) -> str:
    """Validate club ID"""
    if not club_id or not club_id.strip():
        raise ValueError("club_id is required")
    
    club_id = club_id.strip()
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', club_id):
        raise ValueError(f"Invalid club_id format: {club_id}")
    
    return club_id


def validate_tournament_id(tournament_id: str) -> str:
    """Validate tournament ID"""
    if not tournament_id or not tournament_id.strip():
        raise ValueError("tournament_id is required")
    
    tournament_id = tournament_id.strip()
    
    # Allow alphanumeric, hyphens
    if not re.match(r'^[a-zA-Z0-9-]+$', tournament_id):
        raise ValueError(f"Invalid tournament_id format: {tournament_id}")
    
    return tournament_id


def validate_country_iso(country_iso: str) -> str:
    """Validate ISO 3166-1 alpha-2 country code"""
    if not country_iso or not country_iso.strip():
        raise ValueError("country_iso is required")
    
    country_iso = country_iso.strip().upper()
    
    if not re.match(r'^[A-Z]{2}$', country_iso):
        raise ValueError(f"Invalid country_iso format: {country_iso}. Must be 2-letter ISO code (e.g., 'US', 'FR')")
    
    return country_iso


def validate_match_id(match_id: str) -> str:
    """Validate match ID"""
    if not match_id or not match_id.strip():
        raise ValueError("match_id is required")
    
    return match_id.strip()


# Operation-specific validators

def validate_player_profile(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player profile params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player stats params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_games_current(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player current games params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_games_archives_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player games archives list params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_games_archives(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player games archives params"""
    username = validate_username(params.get('username', ''))
    
    now = datetime.now()
    year = params.get('year', now.year)
    month = params.get('month', now.month)
    
    if not isinstance(year, int):
        raise ValueError(f"year must be integer, got: {type(year).__name__}")
    
    if not isinstance(month, int):
        raise ValueError(f"month must be integer, got: {type(month).__name__}")
    
    if not (2007 <= year <= now.year):
        raise ValueError(f"Invalid year: {year}. Must be between 2007 and {now.year}")
    
    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month: {month}. Must be between 1 and 12")
    
    limit = validate_limit(params.get('limit'), default=50)
    
    return {'username': username, 'year': year, 'month': month, 'limit': limit}


def validate_player_clubs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player clubs params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_matches(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player matches params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_player_tournaments(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate player tournaments params"""
    return {'username': validate_username(params.get('username', ''))}


def validate_titled_players(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate titled players params"""
    valid_titles = ['GM', 'WGM', 'IM', 'WIM', 'FM', 'WFM', 'NM', 'WNM', 'CM', 'WCM']
    title = params.get('title', '').upper()
    
    if not title:
        raise ValueError("title is required")
    
    if title not in valid_titles:
        raise ValueError(f"Invalid title. Must be one of: {', '.join(valid_titles)}")
    
    limit = validate_limit(params.get('limit'), default=50)
    
    return {'title': title, 'limit': limit}


def validate_club_details(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate club details params"""
    return {'club_id': validate_club_id(params.get('club_id', ''))}


def validate_club_members(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate club members params"""
    club_id = validate_club_id(params.get('club_id', ''))
    limit = validate_limit(params.get('limit'), default=50)
    return {'club_id': club_id, 'limit': limit}


def validate_club_matches(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate club matches params"""
    return {'club_id': validate_club_id(params.get('club_id', ''))}


def validate_tournament_details(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tournament details params"""
    return {'tournament_id': validate_tournament_id(params.get('tournament_id', ''))}


def validate_tournament_round(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tournament round params"""
    tournament_id = validate_tournament_id(params.get('tournament_id', ''))
    round_num = params.get('round')
    
    if not round_num or not isinstance(round_num, int):
        raise ValueError("round must be a positive integer")
    
    if round_num < 1:
        raise ValueError(f"round must be >= 1, got: {round_num}")
    
    return {'tournament_id': tournament_id, 'round': round_num}


def validate_tournament_round_group(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tournament round group params"""
    tournament_id = validate_tournament_id(params.get('tournament_id', ''))
    round_num = params.get('round')
    group_num = params.get('group')
    
    if not round_num or not isinstance(round_num, int):
        raise ValueError("round must be a positive integer")
    
    if not group_num or not isinstance(group_num, int):
        raise ValueError("group must be a positive integer")
    
    if round_num < 1:
        raise ValueError(f"round must be >= 1, got: {round_num}")
    
    if group_num < 1:
        raise ValueError(f"group must be >= 1, got: {group_num}")
    
    return {'tournament_id': tournament_id, 'round': round_num, 'group': group_num}


def validate_country_details(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate country details params"""
    return {'country_iso': validate_country_iso(params.get('country_iso', ''))}


def validate_country_players(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate country players params"""
    country_iso = validate_country_iso(params.get('country_iso', ''))
    limit = validate_limit(params.get('limit'), default=50)
    return {'country_iso': country_iso, 'limit': limit}


def validate_country_clubs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate country clubs params"""
    return {'country_iso': validate_country_iso(params.get('country_iso', ''))}


def validate_match_details(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate match details params"""
    return {'match_id': validate_match_id(params.get('match_id', ''))}


def validate_match_board(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate match board params"""
    match_id = validate_match_id(params.get('match_id', ''))
    board_num = params.get('board')
    
    if not board_num or not isinstance(board_num, int):
        raise ValueError("board must be a positive integer")
    
    if board_num < 1:
        raise ValueError(f"board must be >= 1, got: {board_num}")
    
    return {'match_id': match_id, 'board': board_num}


def validate_leaderboards(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate leaderboards params"""
    categories = validate_categories(params.get('categories'))
    # For leaderboards, limit is per category (default 10, max 50)
    limit = validate_limit(params.get('limit'), default=10, maximum=50)
    
    return {'categories': categories, 'limit': limit}


def validate_daily_puzzle(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate daily puzzle params"""
    return {}


def validate_random_puzzle(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate random puzzle params"""
    return {}


def validate_streamers(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate streamers params"""
    limit = validate_limit(params.get('limit'), default=50)
    return {'limit': limit}
