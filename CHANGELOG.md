
















# Changelog

## [1.51.1] - 2025-10-20

### 🔧 Debug mode — I/O previews généralisés + flag truncation + sanitation unifiée
- Enrichissement des step summaries (tous nœuds): `debug_info.inputs_preview`, `debug_info.outputs_preview`, `ctx_keys`.
- `http_tool`: prévisualisation intégrée `__debug_preview` (prompts/params/output), masquée et tronquée.
- Decisions: `debug_preview` avec `input_resolved` + `available_routes` + `route`.
- `details.truncated`: factorisé via `is_truncated_preview` (10KB, marqueurs internes)
- Sanitation centralisée via `sanitize_details_for_log` (PII mask, arrays>50, strings>200, cap ~10KB).

### 🧰 Logs & Crash — PII-safe + bornés
- step_logger: sanitation avant `details_json`, horodatage `utcnow_str()`.
- crash_logger: sanitation des contexts (50–100KB), suffix de troncature.

### 🧱 Robustesse SQLite
- `init_db`: `PRAGMA journal_mode=WAL`, `timeout=5.0` pour réduire les `database is locked`.

### 🧩 Validators & Handlers bootstrap
- `validate_worker_name()` séparé; `validate_params` gère `debug`/`list` proprement.
- Bootstrap transforms: erreurs d’import/registration loguées sur `stderr` sans bloquer le démarrage.

### 📊 Status — métriques compactes, anti-flood
- `status(..., include_metrics=true)` ou `status(..., metrics={include:true, window:"5m|15m|1h|N"})`
- Bloc `metrics` compact (comptes uniquement): `nodes_executed`, `avg_duration_ms`, `errors{...}`, `retries{...}`, `llm_tokens`.
- Fenêtre paramétrable, calcul léger, payload minimal.

### 🧼 Nettoyage
- Suppression du code mort `_utcnow_str` dans `orchestrator_core.py` (usage central `utils.utcnow_str`).

---

## [1.51.0] - 2025-10-20

### 🏗️ REFACTORING P0 COMPLET - Architecture Unifiée & Déduplication

... (entries précédentes inchangées) ...


## [1.51.1] - 2025-10-20

### 🛠 Maintenance & Hotfixes

- feat(transforms): add domain transforms `array_ops`, `date_ops`, `json_ops`, and `array_concat`; auto-register on bootstrap
- refactor(utils): centralize UTC timestamp formatting via utils.time.utcnow_str (single source of truth)
- fix(debug): unify pause/resume path; stable step/continue/run_until with proper ctx diffs and previews
- fix(logging): crash logger robust snapshots + full traceback with locals; step logger size capping and truncation flags
- fix(runner): bootstrap crash logging; DB init (WAL, busy timeout) before reads; inject `worker_name` and `db_file` in worker_ctx
- chore(validators/status): clearer validation errors; compact metrics and debug block in status
- feat(http_tool): lightweight debug previews for inputs/messages/output (masked + truncated)
- chore(ai_curation): prompts and subgraphs updated; Sonar user-only prompts; lower quality threshold stays at 7/10

This patch is backward compatible and contains no breaking changes. Recommended upgrade for improved observability and debug stability.
