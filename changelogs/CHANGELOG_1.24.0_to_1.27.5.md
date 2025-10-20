# Changelog (archive)

Range: 1.24.0 → 1.27.5

This file consolidates release notes between v1.23.0 (inclusive previous archive) and v1.29.0 (covered in a later archive). It recreates the missing history prior to 1.29.0 and after 1.23.0.

---

## [1.27.5] - 2025-10-15
Polish + README updates
- CHANGELOG: add 1.27.5 section (lichess, stockfish)
- README (root): synced highlights

## [1.27.4] - 2025-10-15
Workers Realtime polish + Process preload + VAD hard cut + ringback
- UI/process: split UI files (<7KB), preload Mermaid, robust render retry
- Audio: shared volume slider; default 50%
- VAD: immediate cut + cancel on user speech
- Ringback: skype_like pattern (~400/450 Hz), cadence 2–10s
- KPIs overlay: tasks/call_llm/cycles last hour; auto-refresh
- Seeds: realistic cycles (sleep 10m, LLM 1m)

## [1.26.3] - 2025-10-13
Host Audit connectors + YAML extends
- OS/progiciels connectors (Nginx/Apache/PHP-FPM/Node.js) + Ubuntu firewall/SSH
- Symfony/YAML endpoints extended; docs updated

## [1.26.2] - 2025-10-13
Changelog + README updates (Dev Navigator, CI)
- Changelog: clarify Dev Navigator entries and CI workflow
- Root README synced with tools list

## [1.26.1] - 2025-10-13
Dev Navigator CI: build and publish release index
- GitHub Actions workflow added to build index on release publish
- Upload index.db + manifest.json

## [1.26.0] - 2025-10-13
Dev Navigator (LLM-first, cap 20KB, FS-first)
- New tool "Dev Navigator" (skeleton, anti-flood 20KB, spec+stubs)
- Core stubs: compose/overview/tree/search/outline/open/endpoints/tests
- Services: payload budget manager, pagination, fs_scanner, etc.

## [1.25.2] - 2025-10-13
Dev Navigator open(batch) + spec notes
- open: plan multiple files in one call (paths[] + limit cap 50)
- reject fields=full on open; anchors-only policy

## [1.25.1] - 2025-10-13
Release index consistency checks; prefer release index when available
- Query helpers and manifest handling; query_only=ON

## [1.25.0] - 2025-10-13
Compact overview + endpoints detection; tests inventory stubs
- Overview: langs/SLOC sample, key files; deterministic/paginated
- Endpoints: FastAPI/Flask/Django detection

## [1.24.3] - 2025-10-13
Search (anchors-only, paginated) under strict 20KB cap
- Defaults tightened (limit=20, anchors-only); budget enforced
- regex search across repo; pagination and deterministic ordering

## [1.24.2] - 2025-10-13
Open (fs_requests plan), dir_tree BFS skeleton, compact overview placeholder

## [1.24.1] - 2025-10-13
Outline + Endpoints (Python AST/regex); tests inventory helpers

## [1.24.0] - 2025-10-13
Announce Dev Navigator tool + CI workflow
- README + CHANGELOG: new sections and clarifications

---

Notes
- All changes adhere to file-size policy (<7KB per module) unless explicitly noted.
- This archive is reconstructed from release commits and changelog notes; dates correspond to repository history.
