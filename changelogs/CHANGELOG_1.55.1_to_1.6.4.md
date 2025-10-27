# Changelog

## 1.6.4 — 2025-10-26

Improvements (Py Orchestrator + Workers LLM)
- Config directory-only (workers/<name>/config/) généralisée
  - Runner: merge config/config.json (deep) + config/prompts/*.md (injectés dans metadata.prompts) + CONFIG_DOC.json; hot‑reload.
  - Suppression complète des fichiers de config à la racine des workers.
- API config (py_orchestrator.operation=config)
  - key_path générique (dot + [index] + ["clé.avec.points"]) pour éditer n’importe quel élément JSON à n niveaux.
  - storage:"file": prompts.<name> → config/prompts/<name>.md (auto), sinon deep‑set dans config/config.json; storage:"inline": KV only.
  - set.file: écriture directe de fichiers sous config/ (chroot).
  - remove:true: suppression ciblée (chemin imbriqué) dans metadata et config.json.
- ai_curation_v2
  - Migration complète vers config/ directory‑only; prompts externalisés (fichiers .md).
  - Recâblage steps → worker["prompts"].
  - Purge des vestiges (primary_sites) et pilotage depuis primary_site_caps.
- Refactor tool
  - api_router.py + api_config.py (<7KB) + api.py (alias mince); pas de code mort.

Docs
- README: guide “Workers LLM — meilleures pratiques (config/ dir + prompts fichiers + API config)”, exemples d’édition (key_path, storage, set.file), checklist.

Notes
- Rétro‑compatibilité: les workers existants doivent migrer leur config vers config/ (prompt fichiers + config.json). L’API supporte désormais l’édition fine et la persistance fichier.

---

## 1.6.3 — 2025-10-26

New
- Worker config file (single source of truth): `workers/<worker_name>/config.py`
  - CONFIG (valeurs) + CONFIG_DOC (descriptions lisibles)
  - Priorité: `config.py` > `PROCESS.metadata` (shallow merge)
  - Hot-reload support (les changements sont pris en compte au vol)
  - Nouvelle variable supportée: `http_timeout_sec` (timeout HTTP des calls MCP au niveau worker)
- Tool `py_orchestrator`: nouvelle opération `config`
  - Lecture: retourne `metadata` (valeurs fusionnées) + `docs`
  - Écriture: `set: {key, value}` met à jour la valeur en live (KV) ET persiste dans `workers/<name>/config.py` (bloc CONFIG)

Improvements
- LLM usage & modèles
  - Unwrap non destructif des réponses tool (`env.tool`) — préserve `usage`/`model` autour de `result`
  - Accumulation robuste: support `prompt_tokens`/`completion_tokens`/`total_tokens` (et alias input/output)
  - Fallback modèle sur `params.model` si la réponse tool n’inclut pas `model`
  - `status`: reflète `llm_usage` dans `metrics.llm_tokens` et `metrics.token_llm`
  - Reset des compteurs LLM à chaque `start` (pas d’héritage inter‑run)
- `normalize_llm_output`
  - Tolérant aux JSON partiels/fencés (```json …``` et ``` … ```), réparation des échappements/contrôles, troncature safe, fallback au lieu d’exception
- Transforms catalogue
  - Ajout des headers `TRANSFORM_META` manquants (uci_*, board_coords, pos_to_square, compare_positions, format_template, filter_multi_by_date, dedupe_by_url, idempotency_guard, to_text_list…)
  - Suppression des doublons inutiles (répertoire générique) au profit des variantes `transforms_domain`
- Isolation par run
  - `start`: enregistre `run_id`/`run_started_at`, reset counters LLM
  - Migration DB: `job_steps.run_id` + index + trigger d’auto‑rattachement + backfill (best‑effort)

Fixes
- Timeout LLM: `http_timeout_sec` lu depuis le contexte worker (configurable par worker)
- Statut métriques: plus de désynchronisation entre `llm_usage` et `metrics.llm_tokens`

Docs
- README: section “Worker config (config.py)” + exemples et appel `py_orchestrator.config`

---

## 1.6.2 — 2025-10-26

Improvements (Py Orchestrator: Graph, Debug, Worker DX)
- Graph tool (py_orchestrator.graph)
  - IDs des arêtes désormais toujours qualifiés (SG::STEP) → plus de “liste d’étapes sans flèches”.
  - Conditionnelles rendues en diamant; flèches sortantes labellisées (success, fail, retry, retry_exhausted).
  - Transforms: emoji engrenage (⚙️) systématique; Tools: emojis par catégorie (📊 intelligence, 🗄️ data, 📄 documents, 🎮 entertainment, 🔢 utilities, …).
  - START/END stylés en vert (fill:#d9fdd3, stroke:#2e7d32).
  - render.mermaid=true → renvoie uniquement { mermaid: "..." } (sans nodes/edges verbeux).
- Runner debug/observability
  - execute_step persiste désormais, en cas d’échec, `call` et `last_result_preview` dans job_steps.details_json et en KV (`py.last_call`, `py.last_result_preview`) pour la page status.
  - runner_loop délègue à execute_step (logs et phases cohérents; meilleure traçabilité step-by-step).
- Transforms
  - Nouveau transform `set_value` (utilitaire scalaire).
- Worker ai_curation_v2
  - INIT::STEP_GET_NOW: extraction tolérante de `date.now` (result|content|iso|datetime, imbriqué ou non).
  - COLLECT::STEP_FETCH_NEWS: from_date/to_date au format `YYYY-MM-DD` (conformité Guardian/news_aggregator).

Docs
- README mis à jour: « Python Orchestrator — Guide ultra‑concis pour LLM (worker parfait) » (règles, conventions Mermaid, debug/observabilité, patterns).

## 1.6.1 — 2025-10-25

Fixes / Improvements (Orchestrator debug & stability)
- Deterministic debug on start (enable_on_start): purge transient debug state before enabling step mode to prevent stale handshakes (command/req_id/response_id/last_step/etc.).
- Debug enable/enable_now normalization: clear ephemeral fields to avoid ghost states when enabling at runtime.
- First pause is informative: START now populates a minimal last_step so inspect() doesn’t return an empty step at first pause.
- Previous/current node clarity:
  - Persist previous_node at each pause (previous paused_at),
  - Expose current_node in status: paused → paused_at, running → executing_node.
- Current run filtering:
  - start records run_started_at (and run_id),
  - status error/crash compact view and worker list last_step_at are filtered to the current run when available,
  - metrics also consider run_started_at in addition to the time window.
- Refactor: split api_start_stop into api_start (start) and api_stop (stop) with a thin compatibility wrapper to avoid breaking imports.

Notes
- No DB migration. No API breaking changes.
- stop/kill do not purge debug state (not required with deterministic start); behavior unchanged.

## 1.6.0 — 2025-10-23

Improvements (Minecraft Control / list_entities)
- Robust SNBT parsing and automatic fallback:
  - When full SNBT is not available or braces are unbalanced, the tool now switches to per-field queries (Pos, Rotation, CustomName, id, Tags, Dimension, UUID) and reassembles entities by index.
  - Quote-aware multi-compound extraction supports concatenated outputs like "<name> has the following entity data: {...}" repeated on one line.
- Output fidelity: raw output returned verbatim.
  - New field result.raw contains the full, unmodified server output (no client-side truncation or ellipsis).
  - Removed result.raw_lines (no longer needed).
- Custom name normalization:
  - result.entities[*].custom_name is now normalized (outer quotes removed), e.g. '"wP_a2"' -> 'wP_a2'.
- Optional fields:
  - result.entities[*].type (from NBT id without namespace, e.g. "cat").
  - result.entities[*].uuid when available.
- Module split (<7KB per file) for maintainability:
  - operations/list_entities/api.py — orchestration and response shaping.
  - operations/list_entities/fallback.py — per-field query path and utility splitting.
  - operations/list_entities/fields.py — field decoders and counted fallback extraction.

Notes
- Sorting by distance requires a known center. If a full selector is supplied and relative_to_player=false, center is None and distance sort is a no-op. Provide area.center or rely on relative_to_player=true without a prebuilt selector for distance sorting.

Migration
- No breaking changes to tool spec. Consumers may now rely on result.raw for debugging and on normalized custom_name for grouping.

## 1.55.7 — 2025-10-23

Fixes / Chore
- Dev scripts: remove absolute paths, use only relative paths in scripts/dev.sh and scripts/dev.ps1 (GitHub-friendly, portable).
- Tool spec: vscode_control category fixed to `developer_tools` (LLM dev guide compliance).
- Tool spec: orchestrator displayName updated to `Call LLM`.

## 1.55.6 — 2025-10-23

Chore
- Dependencies updated in pyproject.toml:
  - Added: skyfield

## 1.55.5 — 2025-10-23

Chore
- Dependencies updated in pyproject.toml:
  - Added: yt_dlp, beautifulsoup4 (bs4), websocket-client (websocket), fastapi, uvicorn
- Version bump to 1.55.5

## 1.55.3 — 2025-10-23

Improvements
- Decisions: clearer errors with operand values and types
  - `compare` now reports both operands and their Python types when numeric operators are used on non-numeric values.
  - `enum_from_field` error includes original value + type before normalization.
- Failure logs enriched with IO context
  - On step failure, we now include a debug preview of resolved inputs for io/transform and resolved decision spec + input for decisions.
- Status: remove misleading last_error
  - `status` no longer exposes `last_error` (stale). Errors should be read from `job_steps` (failed steps) and `crash_logs`.
  - `start` clears `last_error` to avoid stale error carry-over between runs.

## 1.55.2 — 2025-10-23

New
- VS Code Control tool added
  - New MCP tool `vscode_control` with operations to open files/folders, diff, manage extensions, settings, search workspace, and preview/apply file changes.

## 1.55.1 — 2025-10-23

Improvements
- Orchestrator Engine: reliable failure logging
  - Per-node exceptions now write a step with status="failed" (job_steps) and a crash entry (crash_logs) with normalized details. Debug pauses are not treated as failures.
- Configurable cycle length ceiling
  - Default max nodes per cycle raised to 1000 and can be configured via env var `ORCHESTRATOR_MAX_NODES_PER_CYCLE`.
- Subgraphs: recursive flattening
  - `flatten_subgraphs` now flattens nested subgraphs recursively before merging into the main graph.
- Validation hardening
  - Reject graphs with more than one `when='always'` edge from the same source node.
- Transforms
  - `format_template`: missing keys now preserve the original `{{placeholder}}` instead of producing unexpected output.
- Housekeeping
  - `debug_utils` switched to clean relative import for `utcnow_str`.

Notes
- Backward compatible. No changes required for existing process files. To change the node traversal ceiling per cycle, set `ORCHESTRATOR_MAX_NODES_PER_CYCLE` in your environment.
