# Changelog

All notable changes to this project will be documented in this file.

**Note**: Older entries have been archived under `changelogs/` (range-based files).

---

## [1.24.0] - 2025-10-13

### Server & Control Panel
- feat(tools): GET /tools now supports compact reload by default to avoid flooding LLMs
  - reload=1 & list=0 (default): returns only {reloaded, tool_count, errors}
  - reload=1 & list=1: returns full list (legacy)
  - no reload: returns list with ETag/304 as before
- docs(methodo): LLM is now explicitly allowed and required to call GET /tools?reload=1 after creating/modifying a tool before running tests.

### astronomy
- fix: enforce <7KB per file by splitting core/constants; no side-effects at import
- feat: implement star_position MVP (bright stars catalog via Skyfield Star)
- feat: celestial_events supports limit with total_count/truncated
- chore: move large constants to JSON under _astronomy/data and lazy-load
- perf: ephemeris cache in <repo>/docs/astronomy
- logs: add INFO/WARNING/ERROR in API

---

## [Unreleased]

- Upcoming audits and tools improvements.

### astronomy (audit cleanup)
- refactor: remove dead code and unused imports (_to_python, calculate_angular_separation import)
- feat: visible_planets now uses `horizon` parameter to compute darkness context; adds `environment` block (sun_altitude_degrees, twilight_horizon_degrees, is_dark_enough)
- feat: sun_moon_times now also returns moonrise/moonset events (in addition to sun and twilight)
- fix: tighten outputs and keep modules <7KB; JSON-serializable formatting kept strict

---

## Archives

- [v1.23.0 Audit Campaign](changelogs/CHANGELOG_1.23.0_audit_campaign.md) - 17 tools audited
- [v1.22.0 to v1.22.2](changelogs/CHANGELOG_1.22.0_to_1.22.2.md)
- [v1.19.0 to v1.21.1](changelogs/CHANGELOG_1.19.0_to_1.21.1.md) - News aggregator, Trivia API, Ollama fixes
- [v1.14.3 to v1.18.2](changelogs/CHANGELOG_1.14.3_to_1.18.2.md)
- [v1.0.0 to 1.13.x](changelogs/CHANGELOG_1.0.0_to_1.13.x.md)
