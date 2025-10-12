# ♟️ Chess.com Tool

Access Chess.com public data API - comprehensive read-only access to players, games, clubs, tournaments, and more.

**Category**: Social & Entertainment  
**Authentication**: None required (public API)  
**Rate Limit**: 100ms between requests (configurable via `CHESS_COM_RATE_LIMIT_DELAY`)

---

## 📋 Operations (24)

### 👤 Player Operations (8)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_player_profile` | Get player public profile (rating, country, status) | `username` | - |
| `get_player_stats` | Get player statistics by game type (rapid, blitz, bullet, daily) | `username` | - |
| `get_player_games_current` | Get player's ongoing games | `username` | - |
| `get_player_games_archives_list` | Get list of monthly archives URLs | `username` | - |
| `get_player_games_archives` | Get player's games for specific month (PGN, results) | `username`, `year`, `month` | `limit` |
| `get_player_clubs` | Get clubs player is member of | `username` | - |
| `get_player_matches` | Get team matches player participated in | `username` | - |
| `get_player_tournaments` | Get tournaments player is currently in | `username` | - |

### 🏆 Titled Players (1)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_titled_players` | Get list of titled players (GM, IM, FM, etc.) | `title` | `limit` |

**Valid titles**: GM, WGM, IM, WIM, FM, WFM, NM, WNM, CM, WCM

### 🏛️ Club Operations (3)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_club_details` | Get club information (name, country, rating, members count) | `club_id` | - |
| `get_club_members` | Get club members list | `club_id` | `limit` |
| `get_club_matches` | Get club team matches | `club_id` | - |

### 🏅 Tournament Operations (3)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_tournament_details` | Get tournament details (name, status, rounds, players) | `tournament_id` | - |
| `get_tournament_round` | Get specific round of tournament (groups, players) | `tournament_id`, `round` | - |
| `get_tournament_round_group` | Get specific group in tournament round (games, standings) | `tournament_id`, `round`, `group` | - |

### 🌍 Country Operations (3)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_country_details` | Get country information (ISO code, name) | `country_iso` | - |
| `get_country_players` | Get players from country | `country_iso` | `limit` |
| `get_country_clubs` | Get clubs from country | `country_iso` | - |

### 🤝 Match Operations (2)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_match_details` | Get team match details (teams, scores, players) | `match_id` | - |
| `get_match_board` | Get specific board from team match (games, results) | `match_id`, `board` | - |

### 📊 Leaderboards (1)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_leaderboards` | Get global leaderboards by category (top 50 per category) | - | `categories`, `limit` |

**Valid categories**: daily, daily960, live_rapid, live_blitz, live_bullet, live_bughouse, live_blitz960, live_threecheck, live_crazyhouse, live_kingofthehill

**Note**: `limit` applies **per category** (default: 10, max: 50)

### 🧩 Puzzle Operations (2)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_daily_puzzle` | Get daily puzzle (FEN, PGN, image) | - | - |
| `get_random_puzzle` | Get random puzzle (FEN, PGN, image) | - | - |

### 📺 Streamer Operations (1)

| Operation | Description | Required Params | Optional Params |
|-----------|-------------|-----------------|-----------------|
| `get_streamers` | Get list of live streamers (Twitch URLs, avatars) | - | `limit` |

---

## 📝 Examples

### Get Player Profile
```json
{
  "operation": "get_player_profile",
  "username": "hikaru"
}
```

**Returns**: Username, title (GM/IM/etc), rating, country, followers, joined date, last online, avatar, Twitch URL

### Get Player Stats
```json
{
  "operation": "get_player_stats",
  "username": "magnuscarlsen"
}
```

**Returns**: Stats per game type (rapid, blitz, bullet, daily) with current rating, wins/losses/draws, best rating/game

### Get Player Games (Monthly Archive)
```json
{
  "operation": "get_player_games_archives",
  "username": "hikaru",
  "year": 2024,
  "month": 10,
  "limit": 100
}
```

**Returns**: Games list with PGN, time control, results, ratings, tournament/match URLs

### Get Titled Players
```json
{
  "operation": "get_titled_players",
  "title": "GM",
  "limit": 50
}
```

**Returns**: List of Grandmaster usernames (50 out of ~2000 total)

### Get Leaderboards (Specific Categories)
```json
{
  "operation": "get_leaderboards",
  "categories": ["live_blitz", "live_bullet"],
  "limit": 20
}
```

**Returns**: Top 20 players per category (40 players total) with rank, username, rating, country, title

### Get Daily Puzzle
```json
{
  "operation": "get_daily_puzzle"
}
```

**Returns**: Title, URL, FEN position, PGN, image URL, publish timestamp

---

## 🎯 Use Cases

### Player Analysis
- Track player rating progress (stats over time)
- Analyze game history (archives by month)
- Study opening repertoire (ECO codes in games)
- Compare players (stats, titles, countries)

### Tournament Monitoring
- Track tournament standings (round by round)
- Get live match results (board by board)
- Find top performers (leaderboards)

### Club Management
- Monitor club members (activity, ratings)
- Track club matches (team performance)
- Compare clubs (size, rating, country)

### Training & Study
- Daily puzzle practice (tactical training)
- Study titled players' games (GM/IM archives)
- Analyze endgame patterns (puzzle database)

### Live Streaming
- Find live streamers (Twitch integration)
- Check if player is streaming (is_streamer flag)

---

## ⚙️ Configuration

### Environment Variables
```bash
# Rate limit delay between requests (seconds)
CHESS_COM_RATE_LIMIT_DELAY=0.1  # Default: 100ms (10 requests/sec)
```

**Chess.com API Guidelines**:
- Max 100 requests per minute recommended
- No authentication required for public data
- User-Agent header required (automatically set)

---

## 🔧 Architecture

```
chess_com.py              # Bootstrap (run + spec)
_chess_com/
  __init__.py             # Exports
  api.py                  # Operation routing + error handling
  core.py                 # Business logic (24 operations)
  validators.py           # Input validation + normalization
  utils.py                # Helpers (timestamps, URLs, formatting)
  services/
    chess_client.py       # HTTP client (rate limiting + retry)
```

---

## ⚠️ Limits & Truncation

| Operation | Default Limit | Max Limit | Truncation Warning |
|-----------|---------------|-----------|-------------------|
| Most operations | 50 | 500 | ✅ Yes |
| `get_leaderboards` | 10/category | 50/category | ✅ Yes |
| Single entity operations | N/A | N/A | No |

**Truncation warnings** are returned when results exceed the limit:
```json
{
  "total_games": 1523,
  "games_returned": 50,
  "games": [...],
  "truncated": true,
  "message": "Showing 50 of 1523 games. Increase 'limit' parameter to see more (max 500)."
}
```

---

## 🚦 Error Handling

| HTTP Status | Error Type | Handling |
|-------------|------------|----------|
| 404 | Resource not found | Clear message (player/club/tournament doesn't exist) |
| 429 | Rate limit exceeded | Retry with exponential backoff (2 retries) |
| 410 | Resource deleted | Permanent deletion message |
| 500+ | Server error | Retry logic (2 attempts) |

All errors return structured JSON:
```json
{
  "error": "Resource not found. The requested player does not exist on Chess.com.",
  "operation": "get_player_profile",
  "params": {"username": "nonexistent"}
}
```

---

## 📚 Resources

- **Chess.com PubAPI**: https://www.chess.com/news/view/published-data-api
- **API Docs**: https://www.chess.com/club/chess-com-developer-community
- **Status Page**: https://status.chess.com/

---

## 🆕 Changelog

### [Unreleased]
- Added comprehensive README documentation
- Added basic logging (info + debug)
- Reduced output verbosity (removed redundant username echoes)
- Fixed regex pattern for username validation in spec

### [Initial]
- 24 operations covering players, clubs, tournaments, matches, countries, leaderboards, puzzles, streamers
- Rate limiting (100ms configurable)
- Retry logic (2 attempts)
- Truncation warnings
- Input validation
