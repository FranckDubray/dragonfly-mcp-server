# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [1.17.2] - 2025-10-12

### Fixed
- **call_llm**: Fixed image path resolution using intelligent project root detection
  - Before: hardcoded `/docs` (system root) causing "file not found" errors
  - After: dynamic path resolution using `Path(__file__).parent.parent.parent`
  - Images under `docs/` now correctly accessible without DOCS_ABS_ROOT env var
  - Support for `DOCS_ABS_ROOT` override maintained for custom setups
- **ollama_local**: Fixed massive log flooding during model download/upload
  - `pull_model` and `push_model` now return concise summaries instead of 500-2000 lines
  - New `_handle_streaming_response()` aggregates progress and returns structured summary
  - Output reduction: 98-99.6% (from thousands of lines to 5-8 lines)
  - Includes download summary with layer count, total size, and completion percentage
  - Prevents LLM context window saturation and improves token efficiency

### Technical Details
- call_llm: `PROJECT_ROOT = Path(__file__).parent.parent.parent` for reliable docs/ discovery
- ollama_local: Streaming response aggregation with human-readable size formatting (e.g., "4.3 GB")
- Both fixes comply with LLM_DEV_GUIDE output size policies

---

## [1.17.1] - 2025-10-11

### Changed
- Remove finnhub tool (insufficient free-tier coverage for Euronext)
- Remove FINNHUB_API_KEY from .env.example
- README back to 37 tools
- Start changelog archival strategy (keep latest at root; archive older entries under changelogs/)
- Remove stray archived changelog placeholder

No tool behavior changes for existing endpoints.

---

## [1.17.0] - 2025-01-11

### Added
- trivia_api tool: Complete Open Trivia Database API access
  - 6 operations: get_questions, list_categories, get_category_count, get_global_count, create_session_token, reset_session_token
  - 24 categories, MCQ and True/False
  - 100% FREE (no API key), unlimited
  - Session token to avoid duplicates
  - Robust encoding handling and HTML entity decoding
  - Shuffled answers + correct index
  - Category question counts by difficulty
  - Category: entertainment

---

## [1.16.0] - 2025-01-11

### Added
- astronomy tool: Skyfield-based astronomy (100% local, no API key)
  - 8 operations: planet_position, moon_phase, sun_moon_times, celestial_events, planet_info, visible_planets, iss_position (placeholder), star_position (placeholder)
  - NASA JPL ephemeris (de421.bsp) auto-downloaded to docs/astronomy/
  - Category: entertainment

### Fixed
- JSON serialization issues for astronomy (numpy types)

---

## [1.15.1] - 2025-01-11

### Fixed
- coingecko tool: output size optimization to respect LLM_DEV_GUIDE rules

---

## [1.15.0] - 2025-01-11

### Added
- open_meteo tool (100% free, no key) — current/hourly/daily forecast, air quality
- coingecko tool — market crypto data (free, no key)
- google_maps tool — geocode/directions/places/timezone/elevation (with GOOGLE_* keys and fallback)
- telegram_bot tool — full Telegram Bot API access

### Changed
- Google API token fallback logic across Google tools

### Removed
- openweathermap tool replaced by open_meteo

---

## [1.14.3] - 2025-10-11

### Added
- device_location tool: Get GPS coordinates and location info for current device
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
- chess_com tool: Complete Chess.com public API access (no authentication required)
  - 24 operations covering all public endpoints
  - Player profiles, stats, games, archives, titled players
  - Club info, country rankings, leaderboards
  - Puzzles, streamers, match results
  - Free tier: no rate limits on public endpoints
  - Category: entertainment
  - Architecture: `_chess_com/` package with proper validators, error handling, and caching

---

For older versions, see: changelogs/ (range-based archives).
