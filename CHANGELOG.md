# Changelog

All notable changes to this project will be documented in this file.

**Note**: Older entries have been archived under `changelogs/` (range-based files).

---

## [Unreleased]

- Planned: further audits and multi-language connectors for Dev Navigator (TS/JS, Go), args_shape normalization, and import graph enhancements.

---

## [1.25.0] - 2025-10-13

### Dev Navigator (LLM-first, panorama + Q&A index)
- feat: Dev Navigator prêt pour la prod côté exploration (compose/overview/tree/search/outline/open/endpoints/tests) — anti-flood 20 KB, anchors-only par défaut, pagination-first, fs_requests pour lecture via FS.
- feat: .gitignore best‑effort dans le scanner (bruit réduit, réponses plus réalistes).
- feat: doc_policy stricte dans open (README/CHANGELOG/docs bloqués par défaut; allow_docs + explicit_allowlist pour lever).
- feat: Q&A index par release (symbol_info, find_callers, find_callees, find_references, call_patterns) — index‑first, cohérence `consistency_mode=require_same_release` via manifest (tag/commit).
- feat(ci): workflow GitHub Actions “on: release” pour construire et publier l’Index Release Pack (`.github/workflows/devnav_index.yml`).
- feat(scripts): `scripts/devnav_build_index.py` (build offline local, met à jour `latest/`).
- feat(builder v1): extraction Python (AST itératif: symbols/methods/classes/UPPERCASE globals, calls/imports, endpoints FastAPI/Flask/Django, dir_stats). Parcours 100% itératif, safe contre RecursionError, assign.value non traversé.
- fix(qna): lazy‑import du reader + split `reader_paths`/`reader_queries` (<7KB/fichier) + PRAGMA `query_only`.
- fix(endpoints): détection FastAPI/Flask itérative (ast.walk), gardes RecursionError.
- refactor(outputs): réponses encore plus concises (pas de `next_cursor` injecté s’il est absent; `stats` seulement si fournie par l’opération; overview compact sans redondance).
- docs: `.env.example` ajoute `DEVNAV_REPO_SLUG` (slug stable, requis serveur/CI).

### Server & Control Panel
- docs(methodo): rappeler GET /tools?reload=1 après création/modif d’un tool avant tests.

---

## [1.24.0] - 2025-10-13

### Server & Control Panel
- feat(tools): GET /tools now supports compact reload by default to avoid flooding LLMs
  - reload=1 & list=0 (default): returns only {reloaded, tool_count, errors}
  - reload=1 & list=1: returns full list (legacy)
  - no reload: returns list with ETag/304 as before

### astronomy
- fix: enforce <7KB per file by splitting core/constants; no side-effects at import
- feat: implement star_position MVP (bright stars catalog via Skyfield Star)
- feat: celestial_events supports limit with total_count/truncated
- chore: move large constants to JSON under _astronomy/data and lazy-load
- perf: ephemeris cache in <repo>/docs/astronomy
- logs: add INFO/WARNING/ERROR in API

---

## Archives

- [v1.23.0 Audit Campaign](changelogs/CHANGELOG_1.23.0_audit_campaign.md) - 17 tools audited
- [v1.22.0 to v1.22.2](changelogs/CHANGELOG_1.22.0_to_1.22.2.md)
- [v1.19.0 to v1.21.1](changelogs/CHANGELOG_1.19.0_to_1.21.1.md) - News aggregator, Trivia API, Ollama fixes
- [v1.14.3 to v1.18.2](changelogs/CHANGELOG_1.14.3_to_1.18.2.md)
- [v1.0.0 to 1.13.x](changelogs/CHANGELOG_1.0.0_to_1.13.x.md)
