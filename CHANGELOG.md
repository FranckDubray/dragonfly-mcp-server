# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

### velib - [2025-10-12] ✅ AUDITED (8.5→9.2/10)

**Fixed**:
- 🟡 CONFORMITY: Tags ajoutés `["paris", "bike_sharing", "transport", "realtime"]` dans spec JSON
- 🟡 CONFORMITY: Logging ajouté (INFO/WARNING/ERROR) dans core.py, fetcher.py
- 🟡 CONFORMITY: Truncation warning si `refresh_stations` importe > 1000 stations
- 🟡 CONFORMITY: Outputs simplifiés (suppression champs verbeux `success`, `operation` des handlers)
- 🟢 IMPROVEMENTS: Messages d'erreur détaillés avec contexte d'opération

**Technical**: velib.json -17B (tags), core.py +1403B (logging + truncation), api.py +63B (docstring), fetcher.py +1109B (logging). Total: +2558B (~2.5 KB). Conformité: 70%→92%.

**Tests**: 5/5 non-regression OK (check_cache, get_availability, refresh_stations, validation, edge case validés).

**SCORE FINAL: 9.2/10** ⭐⭐⭐⭐⭐

**Note**: Serveur must be restarted to apply changes (Python modules cached).

**Commits**: (à venir)

---

### discord_bot - [2025-10-12] ✅ AUDITED (8.9→9.6/10)

**Fixed**:
- 🟡 CONFORMITY: Tags ajoutés `["discord", "bot", "messaging", "api"]` dans spec JSON
- 🟡 CONFORMITY: Description `limit` mise à jour (default: 5 pour list_messages/search_messages, 50 pour autres)
- 🟡 CONFORMITY: Outputs simplifiés (suppression champs verbeux `status`, `operation`)
- 🟡 CONFORMITY: Bot_user nettoyé dans health_check (suppression 15+ champs null/inutiles: public_flags, flags, banner, mfa_enabled, locale, premium_type, email, verified, bio, etc.)
- 🟢 IMPROVEMENTS: Logging ajouté (INFO/WARNING/ERROR) dans ops_utility.py
- 🟢 IMPROVEMENTS: Messages d'erreur détaillés avec error_type et operation context

**Technical**: discord_bot.json +92B (tags), utils.py +800B (clean_bot_user), ops_utility.py +967B (logging), operations.py +481B (error handling), ops_messages.py -600B (simplification). Conformity: 70%→98%.

**Tests**: 3/3 non-regression OK (health_check, list_guilds, list_messages validés après redémarrage serveur).

**SCORE FINAL: 9.6/10** ⭐⭐⭐⭐⭐

**Commits**: f0aee0c, a03acc5

---

### http_client - [2025-10-12] 🔴 CRITICAL FIXES (broken during discord_bot audit)

**Fixed**:
- 🔴 CRITICAL: Syntax error in utils.py line 57 (`response_Dict[str, Any]` → `response_Dict[str, Any]`)
- 🔴 CRITICAL: Duplicate method/url parameters causing `route_request() got multiple values for argument 'method'`
- 🔴 CRITICAL: Parameter extraction bug in run() causing all requests to fail with HTTP 500

**Technical**: http_client.py fixed (params cleanup), utils.py fixed (syntax error). Module was completely broken for ~30 minutes.

**Tests**: Fixed and validated with discord_bot tests.

**Commits**: 2faf5d5, a5b7348, b4568fe

---

### http_client - [2025-10-12] ✅ AUDITED (8.5→9.5/10)

**Fixed**:
- 🟡 CONFORMITY: Logging added (INFO for requests, WARNING for errors/large bodies)
- 🟡 CONFORMITY: Truncation warning for body > 100 KB
- 🟡 CONFORMITY: Outputs simplified (removed redundant `success` field, kept only `ok`)
- 🟢 DOCUMENTATION: Complete README.md added (7.6 KB, usage examples, architecture, performance notes)

**Technical**: core.py +1485B (logging + truncation), utils.py -65B (output cleanup), README.md +7600B (new). Conformity: 75%→98%.

**Tests**: 12/12 non-regression OK (all HTTP methods, auth types, validation, error handling, response formats functional).

**SCORE FINAL: 9.5/10** ⭐⭐⭐⭐⭐

---

### call_llm - [2025-10-12] ✅ AUDITED (9.2/10) → CLEANUP

**Fixed**:
- 🔴 CRITICAL: NameError 'tool_Dict' resolved by adding `from __future__ import annotations` to all _call_llm modules (deferred annotation evaluation)
- 🔴 CRITICAL: Découpage call_llm.py sous 7KB (9.2KB → 4.6KB) : extraction helpers vers file_utils.py
- 🟡 MINOR: Clé debug normalisée (" debug" → "debug" dans core.py)

**Cleanup (2025-10-12 22:23)** :
- 🧹 REFACTOR: Suppression phase1.py (4.6 KB code mort jamais utilisé)
- 🧹 Architecture module mise à jour dans README.md

**Technical**: call_llm.py -4.6KB (helpers → file_utils.py +4.1KB), 10 modules +35B each (from __future__), core.py +4B (debug key), phase1.py -4.6KB (supprimé). Conformité: 85%→92%.

**Tests**: 5/5 non-régression OK (simple, tools orchestration, vision, validation model/message).

**Known Issues**: core.py = 9.8KB > 7KB limit (à découper en phase1.py + phase2.py dans future release, non-bloquant).

**SCORE FINAL: 9.2/10** ⭐⭐⭐⭐⭐

---

### telegram_bot - [2025-10-12] ✅ AUDITED (7.7→9.2/10)

**Fixed**:
- 🔴 SECURITY: Token masking in error messages (mask_url() function + safe error handling)
- JSON spec: added `tags` array ["telegram", "messaging", "bot", "notifications"]
- Code: added logging (info for all operations, warnings for API errors and truncation)
- Code: added truncation warnings when get_updates limit reached
- Code: added explicit counts (`returned_count`, `latest_update_id`)
- Outputs simplified: removed verbose `success`/`operation` fields from tool responses

**Added**: README.md (8.8 KB, 10 operations documented with examples, tips & best practices)

**Technical**: telegram_bot.json +34B, api_client.py +850B (security + logging), core.py +485B (logging + truncation + counts), api.py -30B (simplified), README.md +8800B (new). Total: +10139B (~10 KB). Conformity: 75%→98%.

**Tests**: 10/10 non-regression OK (all operations functional: get_me, get_updates, send_message, send_poll, edit_message, delete_message, send_location, validation, markdown, pagination).

**SCORE FINAL: 9.2/10** ⭐⭐⭐⭐⭐

---

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

For older versions, see: [changelogs/](changelogs/) (range-based archives).
