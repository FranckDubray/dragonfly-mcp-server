# Changelog

## [1.52.0] - 2025-10-21

### ✨ NEW: Excel Row
- **Nouveau tool**: `excel_row` pour manipuler les lignes Excel avec formats avancés
- **Opérations**: insert_row, update_row, delete_row, list_backups, restore_backup
- **Formats Excel**:
  - Number formats: date_iso, date_short_fr, currency_eur_fr, currency_usd_en, accounting_eur_fr, percent_0/2, decimal_2/3, integer, custom
  - Font: name, size (6-72), bold, italic, underline, color
  - Alignment: horizontal/vertical, wrap_text, indent
  - Background color + border (thin/medium/thick)
- **Granularité**: row_format (défaut) + columns_format (overrides par colonne)
- **Parsing dates**: parse.date_input_format (auto/DD/MM/YYYY/YYYY-MM-DD/MM/DD/YYYY) séparé de l'affichage Excel
- **Backups**: création, listing, restauration (docs/office/excel_backups/)
- **Mapping**: clés normalisées ou noms Excel originaux acceptés
- **Support**: colonnes > 26 (A-Z-AA-AZ...)
- **Compatibilité**: params legacy (color, border_color, date_format) mappés automatiquement

Note: Warning Excel "contenu illisible" peut apparaître avec formats complexes (bénin, formats appliqués correctement).

## [1.51.2] - 2025-10-20

### ♻️ Refactor & Stability
- refactor(engine): split orchestrator_core into logical modules (<7KB each)
  - core_nodes_common.py (begin/exec start/end, scope resets)
  - core_nodes_handler.py (IO/transform execution, retries, mapping, debug)
  - core_nodes_decision.py (decisions, debug)
- fix(engine): remove engine/__init__ import side-effects to eliminate circular imports
- chore(start): purge all debug.* flags at start unless debug.enable_on_start=true
- runner: bootstrap hardened (worker_name/db_file injected)

No breaking changes. Improves debuggability and respects file-size guard.

## [1.51.1] - 2025-10-20

### 🛠 Maintenance & Hotfixes
- feat(transforms): add domain transforms `array_ops`, `date_ops`, `json_ops`, and `array_concat`; auto-register on bootstrap
- refactor(utils): centralize UTC timestamp formatting via utils.time.utcnow_str (single source of truth)
- fix(debug): unify pause/resume path; stable step/continue/run_until with proper ctx diffs and previews
- fix(logging): crash logger robust snapshots + full traceback with locals; step logger size capping and truncation flags
- fix(runner): bootstrap crash logging; DB init (WAL, busy timeout) before reads; inject `worker_name` and `db_file` in worker_ctx
- chore(validators/status): clearer validation errors; compact metrics and debug block in status
- feat(http_tool): lightweight debug previews for inputs/messages/output (masked & truncated)
- chore(ai_curation): prompts and subgraphs updated; Sonar user-only prompts; lower quality threshold stays at 7/10

This patch is backward compatible and contains no breaking changes. Recommended upgrade for improved observability and debug stability.
