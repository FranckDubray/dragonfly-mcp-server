# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

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
