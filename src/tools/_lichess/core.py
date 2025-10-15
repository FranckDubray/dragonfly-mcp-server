"""
Core business logic for Lichess public operations (no token)
"""
from typing import Dict, Any, List
from .services.lichess_client import LichessClient


def get_user_profile(username: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/user/{username}")
    # Flatten key info
    perfs = data.get('perfs', {})
    return {
        'id': data.get('id'),
        'username': data.get('username'),
        'title': data.get('title'),
        'online': data.get('online'),
        'createdAt': data.get('createdAt'),
        'seenAt': data.get('seenAt'),
        'perfs': {
            k: {
                'games': v.get('games'),
                'rating': v.get('rating'),
                'rd': v.get('rd'),
                'prog': v.get('prog')
            } for k, v in perfs.items()
        },
        'profile': data.get('profile', {}),
    }


def get_user_perfs(username: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/user/{username}/perf")
    return data


def get_user_teams(username: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/team/of/{username}")
    teams = [{'id': t.get('id'), 'name': t.get('name'), 'nbMembers': t.get('nbMembers')} for t in data]
    return {'teams_count': len(teams), 'teams': teams}


def get_user_current_game(username: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/user/{username}/current-game")
    return data


def get_user_games(username: str, perf_type: str = None, rated: bool = None, max: int = 50) -> Dict[str, Any]:
    c = LichessClient()
    params = {k: v for k, v in {
        'max': max,
        'perfType': perf_type,
        'rated': 'true' if rated else None,
        'moves': 'true',
        'pgnInJson': 'true'
    }.items() if v is not None}
    data = c.get(f"/api/games/user/{username}", params=params)
    # Lichess can return array of games (JSON if pgnInJson=true)
    games: List[Dict[str, Any]] = data if isinstance(data, list) else data.get('currentPageResults', [])
    total = len(games)
    return {
        'total_games': total,
        'games_returned': total,
        'games': [
            {
                'id': g.get('id'),
                'rated': g.get('rated'),
                'speed': g.get('speed'),
                'perf': g.get('perf'),
                'players': g.get('players'),
                'status': g.get('status'),
                'winner': g.get('winner'),
                'pgn': g.get('pgn')
            } for g in games
        ]
    }


def get_team_details(team_id: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/team/{team_id}")
    return {
        'id': data.get('id'),
        'name': data.get('name'),
        'description': data.get('description'),
        'nbMembers': data.get('nbMembers'),
        'leaders': data.get('leaders'),
    }


def get_team_members(team_id: str, limit: int = 50) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/team/{team_id}/users")
    users = data if isinstance(data, list) else []
    total = len(users)
    truncated = total > limit
    users = users[:limit]
    return {
        'total_members': total,
        'members_returned': len(users),
        'members': [{'id': u.get('id'), 'username': u.get('username')} for u in users],
        **({'truncated': True, 'warning': f"Showing {limit} of {total} members. Increase 'limit' (max 500)."} if truncated else {})
    }


def get_tournament_details(tournament_id: str) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/tournament/{tournament_id}")
    return data


def get_tournament_results(tournament_id: str, limit: int = 50) -> Dict[str, Any]:
    c = LichessClient()
    data = c.get(f"/api/tournament/{tournament_id}/results")
    players = data if isinstance(data, list) else []
    total = len(players)
    truncated = total > limit
    players = players[:limit]
    return {
        'total_players': total,
        'players_returned': len(players),
        'players': players,
        **({'truncated': True, 'warning': f"Showing {limit} of {total} players. Increase 'limit' (max 500)."} if truncated else {})
    }


def get_top_players(perf_type: str, count: int = 10) -> Dict[str, Any]:
    # Lichess top players API requires a fixed count per perfType: /api/player/top/{nb}/{perfType}
    # We'll clamp count to [1,50]
    nb = max(1, min(50, count))
    c = LichessClient()
    data = c.get(f"/api/player/top/{nb}/{perf_type}")
    users = data.get('users', [])
    return {
        'perf_type': perf_type,
        'players_returned': len(users),
        'players': [
            {
                'id': u.get('id'),
                'username': u.get('username'),
                'title': u.get('title'),
                'perfs': u.get('perfs', {})
            } for u in users
        ]
    }


def get_daily_puzzle() -> Dict[str, Any]:
    c = LichessClient()
    return c.get("/api/puzzle/daily")


def get_puzzle(puzzle_id: str) -> Dict[str, Any]:
    c = LichessClient()
    return c.get(f"/api/puzzle/{puzzle_id}")
