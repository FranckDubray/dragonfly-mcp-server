# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

### velib - [2025-10-12] ✅ 8.5→9.2/10 ⭐⭐⭐⭐⭐

Tags, logging, truncation warnings, outputs simplifiés. Conformité 70%→92%. Tests: 5/5 OK. Commit: 046abb0

---

### discord_bot - [2025-10-12] ✅ 8.9→9.6/10 ⭐⭐⭐⭐⭐

Tags, outputs simplifiés, bot_user nettoyé (15+ champs supprimés), logging, error handling détaillé. Conformité 70%→98%. Tests: 3/3 OK. Commits: f0aee0c, a03acc5

---

### http_client - [2025-10-12] 🔴 CRITICAL FIXES

Syntax error utils.py, duplicate params, param extraction bug. Module was broken ~30min. Commits: 2faf5d5, a5b7348, b4568fe

---

### http_client - [2025-10-12] ✅ 8.5→9.5/10 ⭐⭐⭐⭐⭐

Logging, truncation warnings, outputs simplifiés, README.md (7.6 KB). Conformité 75%→98%. Tests: 12/12 OK.

---

### call_llm - [2025-10-12] ✅ 9.2/10 ⭐⭐⭐⭐⭐

NameError 'tool_Dict' fixed (`from __future__ import annotations`), call_llm.py découpage < 7KB, phase1.py supprimé (code mort 4.6 KB). Conformité 85%→92%. Tests: 5/5 OK.

**Known Issues**: core.py 9.8KB > 7KB (à découper future release).

---

### telegram_bot - [2025-10-12] ✅ 7.7→9.2/10 ⭐⭐⭐⭐⭐

Token masking, tags, logging, truncation warnings, counts explicites, outputs simplifiés, README.md (8.8 KB). Conformité 75%→98%. Tests: 10/10 OK.

---

### gitbook - [2025-10-12] ✅ 7.2→8.9/10 ⭐⭐⭐⭐

Category, defaults explicites, logging, truncation warnings, counts, validation limites stricte. Conformité 62%→95%. Tests: 10/10 OK.

---

### sqlite_db - [2025-10-12] ✅ 6.6→9.0/10 ⭐⭐⭐⭐⭐

Defaults explicites, tags, `limit` param (default: 100, max: 1000), logging, truncation warnings, counts explicites. Conformité 50%→95%.

---

### academic_research_super - [2025-10-12] ✅ 7.0→8.1/10 ⭐⭐⭐⭐

Defaults explicites, `include_abstracts` param ajouté, arXiv timeout 20s→30s, logging, outputs simplifiés. Conformité 65%→85%.

**Known Issues**: arXiv API timeouts intermittents.

---

### youtube_download - [2025-10-12] ✅ 9.0→9.3/10 ⭐⭐⭐⭐⭐

Defaults explicites, tags, logging. Conformité 88%→93%.

---

### pdf_search - [2025-10-12] ✅ 6.0→8.8/10 ⭐⭐⭐⭐

JSON spec rewrite (match Python impl), `required` fixed, logging, truncation warnings (50 max), counts. Conformité 40%→95%.

---

### date - [2025-10-12] ✅ 6.5→8.5/10 ⭐⭐⭐⭐

spec() loads canonical JSON (was duplicated), descriptions/defaults/examples, validation (format max 100 chars, durations ±10 years), logging, README.md (6.3 KB). Conformité 62%→95%.

---

### chess_com - [2025-10-12] ✅ 8.2→8.8/10 ⭐⭐⭐⭐

`limit` description unified, `username` regex pattern, logging (rate limiting, API errors), README.md (7.6 KB, 24 ops).

**Known Issues**: `/pub/leaderboards` deprecated (404).

---

### random - [2025-10-12] ✨ NEW TOOL

True random generator (RANDOM.ORG atmospheric noise). 7 ops: integers, floats, bytes, coin_flip, dice_roll, shuffle, pick_random. Fallback: Quantum → Atmospheric → CSPRNG. Category: utilities.

---

### ship_tracker - [2025-10-12] ✅ 8.6→9.4/10 ⭐⭐⭐⭐⭐

Truncation warnings, counts (total_detected, matched_filters, returned), timeout 10s→15s, collection limit max 500, logging (WebSocket). Conformité 87%→96%.

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).
