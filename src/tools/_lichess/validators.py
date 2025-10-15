"""
Validation for Lichess tool parameters
"""
from typing import Dict, Any


PERF_TYPES = [
    'ultraBullet', 'bullet', 'blitz', 'rapid', 'classical', 'correspondence',
    'chess960', 'kingOfTheHill', 'threeCheck', 'antichess', 'atomic',
    'horde', 'racingKings'
]


def validate_params(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(params)
    if operation in {'get_user_profile', 'get_user_perfs', 'get_user_teams', 'get_user_current_game', 'get_user_games'}:
        username = p.get('username')
        if not username or not isinstance(username, str):
            raise ValueError("'username' is required and must be a string")
        if operation == 'get_user_games':
            # max default 50, cap 500
            m = p.get('max', 50)
            m = 50 if m is None else int(m)
            if m < 1 or m > 500:
                raise ValueError("'max' must be between 1 and 500")
            p['max'] = m
            perf_type = p.get('perf_type')
            if perf_type:
                if perf_type not in PERF_TYPES:
                    raise ValueError(f"'perf_type' must be one of {PERF_TYPES}")
            rated = p.get('rated')
            if rated is not None and not isinstance(rated, bool):
                raise ValueError("'rated' must be boolean if provided")

    elif operation in {'get_team_details', 'get_team_members'}:
        team_id = p.get('team_id')
        if not team_id or not isinstance(team_id, str):
            raise ValueError("'team_id' is required and must be a string")
        if operation == 'get_team_members':
            limit = int(p.get('limit', 50))
            if limit < 1 or limit > 500:
                raise ValueError("'limit' must be between 1 and 500")
            p['limit'] = limit

    elif operation in {'get_tournament_details', 'get_tournament_results'}:
        tid = p.get('tournament_id')
        if not tid or not isinstance(tid, str):
            raise ValueError("'tournament_id' is required and must be a string")
        if operation == 'get_tournament_results':
            limit = int(p.get('limit', 50))
            if limit < 1 or limit > 500:
                raise ValueError("'limit' must be between 1 and 500")
            p['limit'] = limit

    elif operation == 'get_top_players':
        perf_type = p.get('perf_type')
        if not perf_type or perf_type not in PERF_TYPES:
            raise ValueError(f"'perf_type' is required and must be one of {PERF_TYPES}")
        count = int(p.get('count', 10))
        if count < 1 or count > 50:
            raise ValueError("'count' must be between 1 and 50")
        p['count'] = count

    elif operation == 'get_puzzle':
        pid = p.get('puzzle_id')
        if not pid or not isinstance(pid, str):
            raise ValueError("'puzzle_id' is required and must be a string")

    elif operation == 'get_daily_puzzle':
        pass
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return p
