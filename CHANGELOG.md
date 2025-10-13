























# Changelog

All notable changes to this project will be documented in this file.

**Note**: Older entries have been archived under `changelogs/` (range-based files).

---

## [Unreleased]

- Planned: further audits and multi-language connectors for Dev Navigator (TS/JS, Go), args_shape normalization, and import graph enhancements.

---

## [1.25.1] - 2025-10-13

### Dev Navigator (Q&A + Metrics + Sécurité + Builder)
- feat(metrics): nouvelle opération `metrics` (anti-flood) retournant:
  - total_files / total_bytes
  - files_by_language (trié)
  - sloc_estimate (python, javascript, html, markdown)
  - functions_estimate (python)
- fix(security): chroot FS strict — `path` doit être sous la racine projet (validators). Empêche tout accès hors repo.
- fix(errors): mapping propre des erreurs de validation → `invalid_parameters` (au lieu de `internal_error`).
- feat(spec): spec JSON enrichie (Q&A + metrics). Ajout de `file_path`+`line` pour `symbol_info`, inclusion de `metrics` dans l’enum, descriptions clarifiées. `additionalProperties=false` maintenu.
- feat(endpoints): extractor FastAPI robuste (support `ast.Constant` pour strings).
- feat(builder):
  - scan “git-tracked only” (`git ls-files`) — pas de scan des libs/env/artefacts.
  - exclusions élargies en fallback `os.walk`: `.venv`/`venv`/`env`/`.direnv`/`.tox`/`sqlite3`/`docs`/`static`/`changelogs`…
  - overwrite propre de l’index (supprime `index.db`, `-wal`, `-shm`) avant rebuild.
  - ne stocke pas le code source (métadonnées/anchors uniquement).
- feat(reader): résolution de l’index plus robuste (priorité `git_root/sqlite3`, fallback `CWD/sqlite3`, puis `repo_path/sqlite3`).
  - logs d’erreur enrichis (bases/variantes essayées, chemin exact attendu).
- chore: code mort supprimé (snippetizer non utilisé).

### Notes
- Q&A nécessite `./sqlite3/<slug>/<tag>__<sha8>/index.db` (ou `./sqlite3/<slug>/latest/`).
- L’index est désormais rapide à construire, compact et strictement limité au code versionné.

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
