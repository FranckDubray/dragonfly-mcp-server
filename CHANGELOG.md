# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [1.17.3] - 2025-10-12

### Fixed
- **ollama_local**: Vision support simplified and clarified
  - `operation=generate` now properly documented as THE way to use images
  - `operation=chat` explicitly rejects images with helpful error message pointing to `generate`
  - Removed broken auto-switch logic that was confusing and non-functional
  - Clear documentation: `generate` = images OK, `chat` = text only
  - Example error message guides users to correct usage

### Changed
- **ollama_local**: Massive output cleanup for better LLM token efficiency
  - `generate` response: removed `context` array (internal tokens), raw duration fields
  - `chat` response: same cleanup, keep only essential fields
  - Before: 15+ fields including internal state
  - After: 6 essential fields (success, response/message, model, timing, token counts)
  - Human-readable durations: "12.3s" instead of nanoseconds
  - Output reduction: ~70% fewer tokens for typical responses

### Technical Details
- ollama_local spec: Enhanced descriptions for `generate` vs `chat` operations
- Image support: `image_files` parameter works perfectly with `generate` operation
- Vision models tested: llava:13b confirmed working with local images under docs/
- Error messages: Actionable suggestions with example payloads

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

For older versions, see: changelogs/ (range-based archives).
