



# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

### youtube_download - [2025-10-12] ✅ AUDITED (9.0→9.3/10)

**Fixed**:
- JSON spec: added explicit defaults for `operation`, `media_type`, `quality`, `max_duration`, `timeout`
- JSON spec: added `tags` array for better UI filtering
- Logging added: info for download start/complete, warnings for invalid inputs/duration exceeded
- Output slightly improved: `handle_get_info()` and `handle_download()` return cleaner dicts

**Improved**:
- Default values now explicit in JSON (LLM can see them directly)
- Better discoverability via tags: `youtube`, `video`, `audio`, `download`, `transcription`

**Technical Details**:
- youtube_download.json: +397B (1918→2315B)
- core.py: +1026B (5768→6794B)
- Conformity: 88% → 93%

**Tests**:
- ✅ Test 1: get_info (valid URL) → metadata retrieved successfully (Rick Astley video)
- ✅ Test 2: get_info (invalid URL) → validation error with clear message

**Audit Results**:

| Critère | Avant | Après |
|---------|-------|-------|
| JSON Spec LLM | 9/10 | 10/10 |
| Architecture | 10/10 | 10/10 |
| Sécurité | 9/10 | 9/10 |
| Robustesse | 9/10 | 9/10 |
| Conformité | 7/10 | 9/10 |
| Performance | 9/10 | 9/10 |
| Maintenabilité | 10/10 | 10/10 |
| Documentation | 9/10 | 9/10 |

**SCORE FINAL: 9.3/10** ⭐⭐⭐⭐⭐

**Notes**: Tool déjà excellent avant audit. Architecture exemplaire (séparation api/core/validators/utils/services). Correctifs mineurs uniquement (defaults explicites, tags, logging).

---

### pdf_search - [2025-10-12] ✅ AUDITED (6.0→8.8/10)

**Fixed**:
- JSON spec completely rewritten to match Python implementation (was totally inconsistent)
- `required` now includes `["operation", "query"]`
- All parameters documented: `query`, `path/paths`, `pages`, `pages_list`, `case_sensitive`, `regex`, `recursive`, `context`
- `context` parameter validated (0-500 range, default 80)
- Output simplified: removed verbose metadata (`success`, `searched_files`)
- Logging added: warnings for invalid paths/regex, info for search progress

**Improved**:
- Truncation warnings: clear message when results capped at 50
- Counts clarified: `total_matches` vs `returned_count`
- Summary now optional (only added for multi-file searches or errors)

**Technical Details**:
- pdf_search.json: +699B (1727→2426B)
- pdf_search.py: +1115B (8927→10042B)
- Conformity: 40% → 95%

**Tests**:
- ✅ Test 1: search (query="model", pages="1-3") → 0 matches (correct)
- ✅ Test 2: search (query="the", pages="1") → 45 matches with context snippets
- ✅ Test 3: search (query="the", pages="1-3") → 125 total, 50 returned, truncation warning

**Audit Results**:

| Critère | Avant | Après |
|---------|-------|-------|
| JSON Spec LLM | 3/10 | 9/10 |
| Architecture | 7/10 | 8/10 |
| Sécurité | 8/10 | 8/10 |
| Robustesse | 7/10 | 9/10 |
| Conformité | 4/10 | 10/10 |
| Performance | 8/10 | 9/10 |
| Maintenabilité | 6/10 | 8/10 |
| Documentation | 5/10 | 9/10 |

**SCORE FINAL: 8.8/10** ⭐⭐⭐⭐

---

### date - [2025-10-12] ✅ AUDITED (6.5→8.5/10)

**Fixed**:
- spec() now loads canonical JSON (was duplicated in Python)
- JSON spec clarified: descriptions, defaults, examples added
- Validation: format max 100 chars, durations ±10 years
- Logging: warnings for invalid timezone, large deltas

**Added**: README.md (6.3 KB, 9 operations, use cases)

**Technical**: date.py -1347B, date.json +1937B, _date_README.md +6376B. Conformity 62%→95%.

---

### chess_com - [2025-10-12] ✅ AUDITED (8.2→8.8/10)

**Fixed**:
- `limit` param description unified (was confusing for LLM)
- `username` regex pattern added to JSON spec

**Added**:
- README.md (7.6 KB, 24 operations, use cases)
- Logging: rate limiting, API errors

**Known Issues**: `/pub/leaderboards` endpoint deprecated by Chess.com (404, confirmed via Perplexity)

---

### random - [2025-10-12] ✨ NEW TOOL

True random number generator using physical sources (RANDOM.ORG atmospheric noise). 7 operations: integers, floats, bytes, coin_flip, dice_roll, shuffle, pick_random. Auto-fallback: Quantum → Atmospheric → CSPRNG. Category: utilities.

---

### ship_tracker - [2025-10-12] ✅ AUDITED (8.6→9.4/10)

**Fixed**:
- Truncation warnings added (LLM now knows when results are limited)
- Counts clarified: total_detected, matched_filters, returned
- Default timeout 10s→15s (better for slow ships)
- Collection limit: max 500 ships (safety)

**Added**: Logging (WebSocket events, warnings)

**Technical**: core.py +1201B, aisstream.py +1570B. Conformity 87%→96%.

---

### discord_bot - [2025-10-12] ✅ AUDITED (8.6→9.6/10)

**Fixed**:
- `list_guilds` operation added to spec (was missing in enum)
- Message cleaning less aggressive (preserves context fields)
- Truncation warnings for `list_messages`

**Added**: README.md (29 operations documented)

**Technical**: discord_bot.json +27B, utils.py +915B. Conformity 95%→98%.

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).

 
 
 
