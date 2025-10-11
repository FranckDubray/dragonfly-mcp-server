# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

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

For older versions, see: changelogs/CHANGELOG_1.0.0_to_1.13.x.md and future archives.
