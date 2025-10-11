# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

---

## [1.15.1] - 2025-01-11

### Fixed
- **coingecko** tool: Output size optimization to respect LLM_DEV_GUIDE rules
  - `get_market_chart`: Limit to max 100 data points (sample if >100), add truncation warning
  - `get_coin_info`: Remove developer_data, limit categories to 5, truncate description to 300 chars
  - `list_coins`: Add warning message when truncated
  - All operations now return `total_count` vs `returned_count` when applicable
  - Prevents overwhelming LLMs with massive datasets (1000+ items)

---

## [1.15.0] - 2025-01-11

### Added
- **open_meteo** tool: Complete weather data via Open-Meteo API (open source)
  - **6 operations**: current_weather, forecast_hourly, forecast_daily, air_quality, geocoding, reverse_geocoding
  - Current weather, hourly forecast (168h/7d), daily forecast (16d), air quality (European AQI)
  - Geocoding/reverse geocoding integrated
  - **100% FREE**: No API key required, unlimited for non-commercial use
  - Category: utilities
  - Architecture: `_open_meteo/` (api, core, validators, utils, services/api_client)

- **coingecko** tool: Complete cryptocurrency data via CoinGecko API
  - **10 operations**: get_price, get_coin_info, search_coins, get_market_chart, get_trending, get_global_data, list_coins, get_exchanges, get_coin_history, compare_coins
  - Real-time prices, market data, historical charts, trending coins, global crypto stats
  - Exchange rankings, coin search, multi-coin comparison
  - Free tier: 50 calls/min, **no API key required**
  - Category: data
  - Architecture: `_coingecko/` (api, core, validators, utils, services/api_client)

- **google_maps** tool: Complete Google Maps API access
  - **9 operations**: geocode, reverse_geocode, directions, distance_matrix, places_search, place_details, places_nearby, timezone, elevation
  - Geocoding (address ↔ coordinates), directions (driving/walking/transit/bicycling)
  - Distance matrix (multiple origins/destinations), places search/nearby/details
  - Timezone, elevation data
  - Free tier: $200 credit/month (~28,000 geocoding requests)
  - Requires: GOOGLE_MAPS_API_KEY or **GOOGLE_API_KEY (fallback)**
  - Category: utilities
  - Architecture: `_google_maps/` (api, core, validators, utils, services/api_client with fallback token logic)

- **telegram_bot** tool: Complete Telegram Bot API access
  - **10 operations**: send_message, send_photo, send_document, send_location, send_video, get_updates, get_me, delete_message, edit_message, send_poll
  - Send messages (text/Markdown/HTML), photos, documents, videos, locations
  - Read updates (long polling), edit/delete messages, polls
  - Free and unlimited
  - Requires: TELEGRAM_BOT_TOKEN
  - Category: communication
  - Architecture: `_telegram_bot/` (api, core, validators, utils, services/api_client)

### Changed
- **Google API token fallback logic**: All Google services (YouTube, Google Maps) now support fallback to GOOGLE_API_KEY if specific key not set
  - Priority: GOOGLE_MAPS_API_KEY (specific) → GOOGLE_API_KEY (generic fallback)
  - Example: youtube_search uses YOUTUBE_API_KEY → GOOGLE_API_KEY
  - Simplifies configuration for users with single Google API key

### Removed
- **openweathermap** tool: Replaced by open_meteo (OpenWeatherMap requires credit card even for free tier)
  - open_meteo is 100% free, no registration required, open source

---

## [1.14.3] - 2025-10-11

### Added
- **device_location** tool: Get GPS coordinates and location info for current device
  - IP-based geolocation (free, no API key required)
  - Returns: latitude, longitude, city, region, country, timezone, ISP, ASN
  - 2 providers with automatic fallback: ipapi.co (default), ip-api.com
  - Accuracy: city/region level (~1-5 km radius)
  - Category: utilities

### Removed
- Control panel (/control): removed non-working tag filters (chips) and tag bar entirely
  - Tags are no longer displayed, used, or loaded in the UI
  - HTML markup for tags box removed from ui_html.py
  - JavaScript tag filtering logic removed from search.js
- Tool list sidebar: removed technical name badge for cleaner appearance
  - Technical name still visible in detailed tool view header

### Changed
- Control panel search simplified to text-only filtering
  - Clean text search across tool names and categories
  - No tag chips, no complex filtering UI
- UI/UX improvements for category and tool distinction
  - Category headers: bolder typography, gradient backgrounds, left border accent, shadow
  - Tool items: white background, subtle indent, smooth hover animations
  - Clear visual hierarchy: categories stand out, tools clearly nested
- Complete design overhaul to match portal branding
  - Primary color: green (#10b981) matching portal badges
  - Header: gradient green background with Dragonfly emoji (🐉)
  - Clean white/light gray color scheme (#fafafa, #ffffff)
  - Soft shadows and subtle borders throughout
  - Modern card-based layout with professional spacing
  - Typography and transitions aligned with portal aesthetic

---

## [1.14.2] - 2025-10-11

### Added
- UI (/control) tag filters for external knowledge tools (chips): `external_sources`, `knowledge`, `social`, `scraping`, `docs`, `search`, `api`, `video`, `pdf`.
- Tags in tool specs for external knowledge cluster:
  - academic_research_super: [knowledge, research, external_sources]
  - reddit_intelligence: [social, knowledge, scraping, external_sources]
  - gitbook: [knowledge, docs, search]

### Fixed
- sqlite_db category explicitly set to `data`.
- discord_webhook category consistently set to `communication` in JSON and Python spec_def.

### Changed
- LLM_DEV_GUIDE.md clarifies use of `tags` to mark external knowledge base tools while keeping the 10 canonical categories unchanged.
- README updated: control panel UX notes and canonical categories fully reflected.

---

## [1.14.1] - 2025-10-11

### Fixed
- Categories alignment across all tools — enforced the 10 canonical categories in all JSON specs
  - math, date → utilities
  - http_client → networking
  - ship_tracker → transportation (and added `timeout.default: 10`)
  - velib → transportation (was "infrastructure")
  - pdf_download, pdf_search, pdf2text, office_to_pdf, universal_doc_scraper → documents
  - generate_edit_image → media (category added)
- UI (/control): professional ergonomics improvements
  - Clear separation of categories vs tools
  - Categories are collapsed by default (clean overview)
  - Favorites (★/☆) with persistence
  - Category badges in tool header, technical name badge
  - Keyboard shortcuts: `/` focus search, Ctrl/Cmd+Enter execute
  - Last selected tool restored

### Changed
- README.md and src/tools/README.md updated to reflect the exact 10 canonical categories
- LLM_DEV_GUIDE.md clarified: categories are mandatory, must be chosen from the 10 canonical keys; UI label for `entertainment` is "Social & Entertainment"

---

## [1.14.0] - 2025-01-11

### Added
- **chess_com** tool: Complete Chess.com public API access (no authentication required)
  - **24 operations** covering all public endpoints
  - Player profiles, stats, games, archives, titled players
  - Club info, country rankings, leaderboards
  - Puzzles, streamers, match results
  - Free tier: no rate limits on public endpoints
  - Category: entertainment
  - Architecture: `_chess_com/` package with proper validators, error handling, and caching

---
