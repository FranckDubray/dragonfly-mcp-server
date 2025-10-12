# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

### gitbook - [2025-10-12] ✅ AUDITED (7.2→8.9/10)

**Fixed**:
- JSON spec: added `category: development`, explicit `default` values (max_results: 10, max_pages: 20)
- Code: added logging (info, warnings) for all operations
- Code: added truncation warnings when results capped (discover_site, search_site)
- Code: added explicit counts (`total_count` vs `returned_count`)
- Code: validation stricte des limites (max_pages ≤ 100, max_results ≤ 50)
- Outputs simplified: removed verbose metadata (`success`, `urls_tested`, `docs_found`)

**Technical**: gitbook.json +39B, gitbook.py +2386B, discovery.py +73B. Conformité 62%→95%.

**Tests**: 10/10 non-régression OK.

**SCORE FINAL: 8.9/10** ⭐⭐⭐⭐

---

### sqlite_db - [2025-10-12] ✅ AUDITED (6.6→9.0/10)

**Fixed**:
- JSON spec: explicit `default` values, `tags` array, `limit` parameter (default: 100, max: 1000)
- Code: logging, truncation warnings for SELECT queries
- Code: explicit counts (`returned_count`, `total_count` if truncated)
- Outputs: replaced `rows_count` with `returned_count`

**Technical**: sqlite_db.json +491B, sqlite_db.py +4712B. Conformité 50%→95%.

**SCORE FINAL: 9.0/10** ⭐⭐⭐⭐⭐

---

### academic_research_super - [2025-10-12] ✅ AUDITED (7.0→8.1/10)

**Fixed**:
- JSON spec: explicit `default` values, missing `include_abstracts` parameter
- Code: arXiv timeout 20s→30s, logging added, outputs simplified

**Technical**: academic_research_super.json +401B, academic_research_super.py +1045B. Conformité 65%→85%.

**Known Issues**: arXiv API timeouts intermittents (30s should suffice, network-side issue).

**SCORE FINAL: 8.1/10** ⭐⭐⭐⭐

---

### youtube_download - [2025-10-12] ✅ AUDITED (9.0→9.3/10)

**Fixed**:
- JSON spec: explicit defaults, `tags` array
- Code: logging (info/warnings), outputs improved

**Technical**: youtube_download.json +397B, core.py +1026B. Conformity 88%→93%.

**SCORE FINAL: 9.3/10** ⭐⭐⭐⭐⭐

---

### pdf_search - [2025-10-12] ✅ AUDITED (6.0→8.8/10)

**Fixed**:
- JSON spec: complete rewrite to match Python implementation
- `required` now includes `["operation", "query"]`
- Code: logging, truncation warnings (50 results max), counts clarified

**Technical**: pdf_search.json +699B, pdf_search.py +1115B. Conformity 40%→95%.

**SCORE FINAL: 8.8/10** ⭐⭐⭐⭐

---

### date - [2025-10-12] ✅ AUDITED (6.5→8.5/10)

**Fixed**:
- spec() now loads canonical JSON (was duplicated in Python)
- JSON spec: descriptions, defaults, examples added
- Validation: format max 100 chars, durations ±10 years
- Logging: warnings for invalid timezone, large deltas

**Added**: README.md (6.3 KB, 9 operations).

**Technical**: date.py -1347B, date.json +1937B. Conformity 62%→95%.

**SCORE FINAL: 8.5/10** ⭐⭐⭐⭐

---

### chess_com - [2025-10-12] ✅ AUDITED (8.2→8.8/10)

**Fixed**:
- `limit` param description unified
- `username` regex pattern added to JSON spec
- Logging: rate limiting, API errors

**Added**: README.md (7.6 KB, 24 operations).

**Known Issues**: `/pub/leaderboards` endpoint deprecated by Chess.com (404).

**SCORE FINAL: 8.8/10** ⭐⭐⭐⭐

---

### random - [2025-10-12] ✨ NEW TOOL

True random number generator using physical sources (RANDOM.ORG atmospheric noise). 7 operations: integers, floats, bytes, coin_flip, dice_roll, shuffle, pick_random. Auto-fallback: Quantum → Atmospheric → CSPRNG. Category: utilities.

---

### ship_tracker - [2025-10-12] ✅ AUDITED (8.6→9.4/10)

**Fixed**:
- Truncation warnings, counts clarified (total_detected, matched_filters, returned)
- Default timeout 10s→15s, collection limit: max 500 ships
- Logging (WebSocket events, warnings)

**Technical**: core.py +1201B, aisstream.py +1570B. Conformity 87%→96%.

**SCORE FINAL: 9.4/10** ⭐⭐⭐⭐⭐

---

### discord_bot - [2025-10-12] ✅ AUDITED (8.6→9.6/10)

**Fixed**:
- `list_guilds` operation added to spec (was missing in enum)
- Message cleaning less aggressive (preserves context fields)
- Truncation warnings for `list_messages`

**Added**: README.md (29 operations documented).

**Technical**: discord_bot.json +27B, utils.py +915B. Conformity 95%→98%.

**SCORE FINAL: 9.6/10** ⭐⭐⭐⭐⭐

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).
