"""
Shared utility functions
"""
from datetime import datetime
from typing import Optional, Dict, Any


def timestamp_to_iso(timestamp: Optional[int]) -> Optional[str]:
    """Convert Unix timestamp to ISO 8601 string"""
    if not timestamp:
        return None
    try:
        return datetime.fromtimestamp(timestamp).isoformat()
    except (ValueError, OSError):
        return None


def extract_country_code(country_url: Optional[str]) -> Optional[str]:
    """
    Extract country code from Chess.com country URL
    Example: https://api.chess.com/pub/country/FR -> FR
    """
    if not country_url:
        return None
    return country_url.rstrip('/').split('/')[-1]


def extract_username(player_url: Optional[str]) -> Optional[str]:
    """
    Extract username from Chess.com player URL
    Example: https://api.chess.com/pub/player/hikaru -> hikaru
    """
    if not player_url:
        return None
    return player_url.rstrip('/').split('/')[-1]


def format_pgn(pgn_string: str) -> Dict[str, Any]:
    """
    Parse PGN string into structured data
    Returns dict with 'headers' and 'moves'
    """
    if not pgn_string or not pgn_string.strip():
        return {'headers': {}, 'moves': ''}
    
    lines = pgn_string.strip().split('\n')
    headers = {}
    moves = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            # Parse header: [Key "Value"]
            content = line[1:-1]
            if ' "' in content:
                key, value = content.split(' "', 1)
                headers[key] = value.rstrip('"')
        elif line and not line.startswith('['):
            # Moves line
            moves.append(line)
    
    return {
        'headers': headers,
        'moves': ' '.join(moves),
    }


def build_chess_com_url(path: str) -> str:
    """Build full Chess.com API URL"""
    base = "https://api.chess.com"
    if not path.startswith('/'):
        path = '/' + path
    return f"{base}{path}"


def format_game_result(result: Optional[str]) -> Optional[str]:
    """
    Normalize game result
    1-0, 0-1, 1/2-1/2, etc.
    """
    if not result:
        return None
    
    result_map = {
        'win': '1-0',
        'checkmated': '0-1',
        'agreed': '1/2-1/2',
        'repetition': '1/2-1/2',
        'timeout': None,
        'resigned': None,
        'stalemate': '1/2-1/2',
        'insufficient': '1/2-1/2',
        '50move': '1/2-1/2',
    }
    
    return result_map.get(result.lower(), result)


def format_time_class(time_class: Optional[str]) -> Optional[str]:
    """
    Normalize time class
    bullet, blitz, rapid, daily, etc.
    """
    if not time_class:
        return None
    return time_class.lower().replace('chess_', '')


def safe_get(data: Dict[str, Any], *keys, default=None) -> Any:
    """
    Safely get nested dict value
    Example: safe_get(data, 'user', 'stats', 'rating', default=0)
    """
    try:
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        return data if data is not None else default
    except (KeyError, TypeError, AttributeError):
        return default
