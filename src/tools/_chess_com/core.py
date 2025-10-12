"""
Core business logic for Chess.com operations
"""
from typing import Dict, Any, List
from .services.chess_client import ChessComClient
from . import utils


# ============================================================================
# PLAYERS
# ============================================================================

def get_player_profile(username: str) -> Dict[str, Any]:
    """Get player public profile"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}")
    
    return {
        'player_id': data.get('player_id'),
        'title': data.get('title'),
        'status': data.get('status'),
        'name': data.get('name'),
        'avatar': data.get('avatar'),
        'country': utils.extract_country_code(data.get('country')),
        'location': data.get('location'),
        'followers': data.get('followers'),
        'is_streamer': data.get('is_streamer', False),
        'twitch_url': data.get('twitch_url'),
        'joined': utils.timestamp_to_iso(data.get('joined')),
        'last_online': utils.timestamp_to_iso(data.get('last_online')),
        'league': data.get('league'),
        'url': data.get('url'),
    }


def get_player_stats(username: str) -> Dict[str, Any]:
    """Get player statistics"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/stats")
    
    # Format stats per game type
    stats_formatted = {}
    game_types = ['chess_rapid', 'chess_blitz', 'chess_bullet', 'chess_daily']
    
    for game_type in game_types:
        if game_type in data:
            game_data = data[game_type]
            last_data = game_data.get('last', {})
            record = game_data.get('record', {})
            best = game_data.get('best', {})
            
            stats_formatted[game_type.replace('chess_', '')] = {
                'rating': last_data.get('rating'),
                'date': utils.timestamp_to_iso(last_data.get('date')),
                'wins': record.get('win', 0),
                'losses': record.get('loss', 0),
                'draws': record.get('draw', 0),
                'best_rating': best.get('rating'),
                'best_date': utils.timestamp_to_iso(best.get('date')),
                'best_game_url': best.get('game'),
            }
    
    # Puzzle stats
    puzzle_stats = {}
    if 'tactics' in data:
        tactics = data['tactics']
        puzzle_stats['tactics'] = {
            'rating': tactics.get('highest', {}).get('rating'),
            'date': utils.timestamp_to_iso(tactics.get('highest', {}).get('date')),
        }
    
    if 'puzzle_rush' in data:
        puzzle_rush = data['puzzle_rush']
        puzzle_stats['puzzle_rush'] = {
            'best_score': puzzle_rush.get('best', {}).get('score'),
            'best_date': utils.timestamp_to_iso(puzzle_rush.get('best', {}).get('date')),
        }
    
    return {
        'stats': stats_formatted,
        'puzzles': puzzle_stats,
        'fide': data.get('fide'),
    }


def get_player_games_current(username: str) -> Dict[str, Any]:
    """Get player's ongoing games"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/games")
    
    games = []
    for game in data.get('games', []):
        games.append({
            'url': game.get('url'),
            'move_by': utils.timestamp_to_iso(game.get('move_by')),
            'pgn': game.get('pgn'),
            'time_control': game.get('time_control'),
            'last_activity': utils.timestamp_to_iso(game.get('last_activity')),
            'white': utils.extract_username(game.get('white')),
            'black': utils.extract_username(game.get('black')),
            'fen': game.get('fen'),
        })
    
    return {
        'games_count': len(games),
        'games': games,
    }


def get_player_games_archives_list(username: str) -> Dict[str, Any]:
    """Get list of available monthly archives URLs for player"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/games/archives")
    
    archives = data.get('archives', [])
    
    return {
        'archives_count': len(archives),
        'archives': archives,
    }


def get_player_games_archives(username: str, year: int, month: int, limit: int = 50) -> Dict[str, Any]:
    """Get player's games for specific month"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/games/{year}/{month:02d}")
    
    all_games = data.get('games', [])
    total_count = len(all_games)
    truncated = total_count > limit
    
    games = []
    for game in all_games[:limit]:
        white = game.get('white', {})
        black = game.get('black', {})
        
        games.append({
            'url': game.get('url'),
            'pgn': game.get('pgn'),
            'time_control': game.get('time_control'),
            'time_class': utils.format_time_class(game.get('time_class')),
            'rules': game.get('rules'),
            'eco': game.get('eco'),
            'end_time': utils.timestamp_to_iso(game.get('end_time')),
            'rated': game.get('rated'),
            'white': {
                'username': white.get('username'),
                'rating': white.get('rating'),
                'result': white.get('result'),
            },
            'black': {
                'username': black.get('username'),
                'rating': black.get('rating'),
                'result': black.get('result'),
            },
            'tournament_url': game.get('tournament'),
            'match_url': game.get('match'),
        })
    
    result = {
        'year': year,
        'month': month,
        'total_games': total_count,
        'games_returned': len(games),
        'games': games,
    }
    
    if truncated:
        result['truncated'] = True
        result['warning'] = f"Showing {limit} of {total_count} games. Increase 'limit' parameter to see more (max 500)."
    
    return result


def get_player_clubs(username: str) -> Dict[str, Any]:
    """Get clubs player is member of"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/clubs")
    
    clubs = []
    for club in data.get('clubs', []):
        # Extract club ID from URL
        club_id = club.get('url', '').rstrip('/').split('/')[-1] if club.get('url') else None
        clubs.append({
            'club_id': club_id,
            'name': club.get('name'),
            'url': club.get('url'),
            'joined': utils.timestamp_to_iso(club.get('joined')),
        })
    
    return {
        'clubs_count': len(clubs),
        'clubs': clubs,
    }


def get_player_matches(username: str) -> Dict[str, Any]:
    """Get team matches player participated in"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/matches")
    
    matches = []
    for match in data.get('matches', []):
        matches.append({
            'name': match.get('name'),
            'url': match.get('url'),
            'start_time': utils.timestamp_to_iso(match.get('start_time')),
            'end_time': utils.timestamp_to_iso(match.get('end_time')),
            'status': match.get('status'),
            'board': match.get('board'),
        })
    
    return {
        'matches_count': len(matches),
        'matches': matches,
    }


def get_player_tournaments(username: str) -> Dict[str, Any]:
    """Get tournaments player is currently in"""
    client = ChessComClient()
    data = client.get(f"/pub/player/{username}/tournaments")
    
    tournaments = []
    for tournament in data.get('tournaments', []):
        tournaments.append({
            'name': tournament.get('name'),
            'url': tournament.get('url'),
            'status': tournament.get('status'),
        })
    
    return {
        'tournaments_count': len(tournaments),
        'tournaments': tournaments,
    }


def get_titled_players(title: str, limit: int = 50) -> Dict[str, Any]:
    """Get list of titled players (GM, IM, etc.)"""
    client = ChessComClient()
    data = client.get(f"/pub/titled/{title}")
    
    all_players = data.get('players', [])
    total_count = len(all_players)
    truncated = total_count > limit
    
    players = all_players[:limit]
    
    result = {
        'title': title,
        'total_players': total_count,
        'players_returned': len(players),
        'players': players,
    }
    
    if truncated:
        result['truncated'] = True
        result['warning'] = f"Showing {limit} of {total_count} players. Increase 'limit' parameter to see more (max 500)."
    
    return result


# ============================================================================
# CLUBS
# ============================================================================

def get_club_details(club_id: str) -> Dict[str, Any]:
    """Get club information"""
    client = ChessComClient()
    data = client.get(f"/pub/club/{club_id}")
    
    return {
        'club_id': data.get('@id'),
        'name': data.get('name'),
        'club_url': data.get('club_url'),
        'description': data.get('description'),
        'country': utils.extract_country_code(data.get('country')),
        'average_daily_rating': data.get('average_daily_rating'),
        'members_count': data.get('members_count'),
        'created': utils.timestamp_to_iso(data.get('created')),
        'last_activity': utils.timestamp_to_iso(data.get('last_activity')),
        'admin': [utils.extract_username(url) for url in data.get('admin', [])],
        'visibility': data.get('visibility'),
        'join_request': data.get('join_request'),
        'icon': data.get('icon'),
    }


def get_club_members(club_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get club members list"""
    client = ChessComClient()
    data = client.get(f"/pub/club/{club_id}/members")
    
    # Chess.com returns members in categories
    all_members = []
    weekly = data.get('weekly', [])
    monthly = data.get('monthly', [])
    all_time = data.get('all_time', [])
    
    # Extract usernames from URLs
    seen = set()
    for member_data in weekly + monthly + all_time:
        username = utils.extract_username(member_data.get('username'))
        if username and username not in seen:
            all_members.append(username)
            seen.add(username)
    
    total_count = len(all_members)
    truncated = total_count > limit
    members = all_members[:limit]
    
    result = {
        'total_members': total_count,
        'members_returned': len(members),
        'members': members,
    }
    
    if truncated:
        result['truncated'] = True
        result['warning'] = f"Showing {limit} of {total_count} members. Increase 'limit' parameter to see more (max 500)."
    
    return result


def get_club_matches(club_id: str) -> Dict[str, Any]:
    """Get club team matches"""
    client = ChessComClient()
    data = client.get(f"/pub/club/{club_id}/matches")
    
    matches = []
    for match in data.get('matches', []):
        matches.append({
            'name': match.get('name'),
            'url': match.get('url'),
            'start_time': utils.timestamp_to_iso(match.get('start_time')),
            'end_time': utils.timestamp_to_iso(match.get('end_time')),
            'status': match.get('status'),
        })
    
    return {
        'matches_count': len(matches),
        'matches': matches,
    }


# ============================================================================
# TOURNAMENTS
# ============================================================================

def get_tournament_details(tournament_id: str) -> Dict[str, Any]:
    """Get tournament details"""
    client = ChessComClient()
    data = client.get(f"/pub/tournament/{tournament_id}")
    
    return {
        'name': data.get('name'),
        'url': data.get('url'),
        'description': data.get('description'),
        'creator': utils.extract_username(data.get('creator')),
        'status': data.get('status'),
        'finish_time': utils.timestamp_to_iso(data.get('finish_time')),
        'settings': data.get('settings'),
        'players': [utils.extract_username(url) for url in data.get('players', [])],
        'rounds': data.get('rounds', []),
    }


def get_tournament_round(tournament_id: str, round: int) -> Dict[str, Any]:
    """Get specific round of tournament"""
    client = ChessComClient()
    data = client.get(f"/pub/tournament/{tournament_id}/{round}")
    
    groups = []
    for group in data.get('groups', []):
        groups.append({
            'name': group.get('name'),
            'url': group.get('url'),
            'players': [utils.extract_username(url) for url in group.get('players', [])],
        })
    
    return {
        'round': round,
        'groups_count': len(groups),
        'groups': groups,
    }


def get_tournament_round_group(tournament_id: str, round: int, group: int) -> Dict[str, Any]:
    """Get specific group in tournament round"""
    client = ChessComClient()
    data = client.get(f"/pub/tournament/{tournament_id}/{round}/{group}")
    
    players = []
    for player_data in data.get('players', []):
        players.append({
            'username': utils.extract_username(player_data.get('username')),
            'points': player_data.get('points'),
            'tie_break': player_data.get('tie_break'),
            'is_advancing': player_data.get('is_advancing', False),
        })
    
    games = []
    for game in data.get('games', []):
        white = game.get('white', {})
        black = game.get('black', {})
        games.append({
            'url': game.get('url'),
            'white': utils.extract_username(white.get('username')),
            'black': utils.extract_username(black.get('username')),
            'time_control': game.get('time_control'),
            'end_time': utils.timestamp_to_iso(game.get('end_time')),
        })
    
    return {
        'round': round,
        'group': group,
        'players_count': len(players),
        'players': players,
        'games_count': len(games),
        'games': games,
    }


# ============================================================================
# COUNTRIES
# ============================================================================

def get_country_details(country_iso: str) -> Dict[str, Any]:
    """Get country information"""
    client = ChessComClient()
    data = client.get(f"/pub/country/{country_iso}")
    
    return {
        'code': data.get('code'),
        'name': data.get('name'),
    }


def get_country_players(country_iso: str, limit: int = 50) -> Dict[str, Any]:
    """Get players from country"""
    client = ChessComClient()
    data = client.get(f"/pub/country/{country_iso}/players")
    
    all_players_urls = data.get('players', [])
    all_players = [utils.extract_username(url) for url in all_players_urls]
    
    total_count = len(all_players)
    truncated = total_count > limit
    players = all_players[:limit]
    
    result = {
        'total_players': total_count,
        'players_returned': len(players),
        'players': players,
    }
    
    if truncated:
        result['truncated'] = True
        result['warning'] = f"Showing {limit} of {total_count} players. Increase 'limit' parameter to see more (max 500)."
    
    return result


def get_country_clubs(country_iso: str) -> Dict[str, Any]:
    """Get clubs from country"""
    client = ChessComClient()
    data = client.get(f"/pub/country/{country_iso}/clubs")
    
    clubs = []
    for club_url in data.get('clubs', []):
        club_id = club_url.rstrip('/').split('/')[-1] if club_url else None
        clubs.append(club_id)
    
    return {
        'clubs_count': len(clubs),
        'clubs': clubs,
    }


# ============================================================================
# MATCHES
# ============================================================================

def get_match_details(match_id: str) -> Dict[str, Any]:
    """Get team match details"""
    client = ChessComClient()
    data = client.get(f"/pub/match/{match_id}")
    
    teams = {}
    for team_key in ['team1', 'team2']:
        if team_key in data:
            team_data = data[team_key]
            teams[team_key] = {
                'name': team_data.get('name'),
                'url': team_data.get('url'),
                'score': team_data.get('score'),
                'result': team_data.get('result'),
                'players': [
                    {
                        'username': utils.extract_username(p.get('username')),
                        'board': p.get('board'),
                        'status': p.get('status'),
                        'played_as_white': p.get('played_as_white'),
                        'played_as_black': p.get('played_as_black'),
                    }
                    for p in team_data.get('players', [])
                ],
            }
    
    return {
        'name': data.get('name'),
        'url': data.get('url'),
        'start_time': utils.timestamp_to_iso(data.get('start_time')),
        'end_time': utils.timestamp_to_iso(data.get('end_time')),
        'status': data.get('status'),
        'boards': data.get('boards'),
        'settings': data.get('settings'),
        'teams': teams,
    }


def get_match_board(match_id: str, board: int) -> Dict[str, Any]:
    """Get specific board from team match"""
    client = ChessComClient()
    data = client.get(f"/pub/match/{match_id}/{board}")
    
    board_scores = data.get('board_scores', {})
    games = []
    
    for game in data.get('games', []):
        white = game.get('white', {})
        black = game.get('black', {})
        
        games.append({
            'url': game.get('url'),
            'pgn': game.get('pgn'),
            'time_control': game.get('time_control'),
            'end_time': utils.timestamp_to_iso(game.get('end_time')),
            'white': {
                'username': white.get('username'),
                'rating': white.get('rating'),
                'result': white.get('result'),
            },
            'black': {
                'username': black.get('username'),
                'rating': black.get('rating'),
                'result': black.get('result'),
            },
            'eco': game.get('eco'),
            'fen': game.get('fen'),
        })
    
    return {
        'board': board,
        'board_scores': board_scores,
        'games_count': len(games),
        'games': games,
    }


# ============================================================================
# LEADERBOARDS
# ============================================================================

def get_leaderboards(categories: List[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Get global leaderboards by category
    
    Args:
        categories: List of categories to return (default: all)
        limit: Number of players per category (default: 10, max: 50)
    
    Returns:
        Dict with leaderboards filtered by categories and limited per category
    """
    client = ChessComClient()
    data = client.get("/pub/leaderboards")
    
    # If no categories specified, return all
    if not categories:
        categories = [
            'daily', 'daily960', 'live_rapid', 'live_blitz', 'live_bullet',
            'live_bughouse', 'live_blitz960', 'live_threecheck', 'live_crazyhouse', 'live_kingofthehill'
        ]
    
    leaderboards = {}
    total_players_returned = 0
    
    for category in categories:
        if category in data:
            # Limit players per category
            all_players_in_category = data[category]
            limited_players = all_players_in_category[:limit]
            
            leaderboard = []
            for player_data in limited_players:
                leaderboard.append({
                    'rank': player_data.get('rank'),
                    'username': player_data.get('username'),
                    'score': player_data.get('score'),
                    'country': utils.extract_country_code(player_data.get('country')),
                    'title': player_data.get('title'),
                    'name': player_data.get('name'),
                    'status': player_data.get('status'),
                    'avatar': player_data.get('avatar'),
                })
            
            leaderboards[category] = leaderboard
            total_players_returned += len(leaderboard)
    
    return {
        'leaderboards': leaderboards,
        'categories_returned': len(leaderboards),
        'total_players_returned': total_players_returned,
        'players_per_category': limit,
    }


# ============================================================================
# PUZZLES
# ============================================================================

def get_daily_puzzle() -> Dict[str, Any]:
    """Get daily puzzle"""
    client = ChessComClient()
    data = client.get("/pub/puzzle")
    
    return {
        'title': data.get('title'),
        'url': data.get('url'),
        'publish_time': utils.timestamp_to_iso(data.get('publish_time')),
        'fen': data.get('fen'),
        'pgn': data.get('pgn'),
        'image': data.get('image'),
    }


def get_random_puzzle() -> Dict[str, Any]:
    """Get random puzzle"""
    client = ChessComClient()
    data = client.get("/pub/puzzle/random")
    
    return {
        'title': data.get('title'),
        'url': data.get('url'),
        'publish_time': utils.timestamp_to_iso(data.get('publish_time')),
        'fen': data.get('fen'),
        'pgn': data.get('pgn'),
        'image': data.get('image'),
    }


# ============================================================================
# STREAMERS
# ============================================================================

def get_streamers(limit: int = 50) -> Dict[str, Any]:
    """Get list of live streamers"""
    client = ChessComClient()
    data = client.get("/pub/streamers")
    
    all_streamers = []
    for streamer in data.get('streamers', []):
        all_streamers.append({
            'username': streamer.get('username'),
            'avatar': streamer.get('avatar'),
            'twitch_url': streamer.get('twitch_url'),
            'url': streamer.get('url'),
            'is_live': streamer.get('is_live', False),
            'is_community_streamer': streamer.get('is_community_streamer', False),
        })
    
    total_count = len(all_streamers)
    truncated = total_count > limit
    streamers = all_streamers[:limit]
    
    result = {
        'total_streamers': total_count,
        'streamers_returned': len(streamers),
        'streamers': streamers,
    }
    
    if truncated:
        result['truncated'] = True
        result['warning'] = f"Showing {limit} of {total_count} streamers. Increase 'limit' parameter to see more (max 500)."
    
    return result
