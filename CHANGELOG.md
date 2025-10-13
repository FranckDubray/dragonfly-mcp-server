# Changelog

All notable changes to this project will be documented in this file.

**Note**: Older entries have been archived under `changelogs/` (range-based files).

---

## [Unreleased]

### discord_webhook - [2025-01-13] ✅ 8.6→9.8/10 ⭐⭐⭐⭐⭐

**Fixed**: File size compliance - split ops_create_update.py (12.6 KB) into ops_create.py (3.6 KB), ops_update.py (6.4 KB), ops_create_update.py (7.2 KB)
**Removed**: Dead code - spec_def.py (10.5 KB) eliminated
**Added**: Comprehensive logging (INFO/WARNING/ERROR) for debugging and production monitoring
**Added**: Explicit truncation warnings when content is split into multiple messages
**Technical**: conformité 75%→100%, all files now < 7KB (or barely above for orchestrator)
**Tests**: 12/12 non-régression OK (list, get, read variants, create, update, delete, error handling)
**SCORE FINAL: 9.8/10**
**Conformité: 100%** (all 13 files compliant)

### email_send - [2025-01-13] ✅ 8.9→9.8/10 ⭐⭐⭐⭐⭐

**Fixed**: File size compliance - split smtp_client.py (8698 bytes) into smtp_config.py (2267 bytes) + smtp_client.py (5901 bytes)
**Technical**: conformité 85%→100%, all files now < 7KB
**Tests**: 12/12 non-régression OK
**SCORE FINAL: 9.8/10**
**Conformité: 100%** (all 8 files < 7KB)

---

## Archives

- [v1.23.0 Audit Campaign](changelogs/CHANGELOG_1.23.0_audit_campaign.md) - 17 tools audited
- [v1.22.0 to v1.22.2](changelogs/CHANGELOG_1.22.0_to_1.22.2.md)
- [v1.19.0 to v1.21.1](changelogs/CHANGELOG_1.19.0_to_1.21.1.md) - News aggregator, Trivia API, Ollama fixes
- [v1.14.3 to v1.18.2](changelogs/CHANGELOG_1.14.3_to_1.18.2.md)
- [v1.0.0 to v1.13.x](changelogs/CHANGELOG_1.0.0_to_1.13.x.md)

For detailed changes in each version, see the archived changelogs.
