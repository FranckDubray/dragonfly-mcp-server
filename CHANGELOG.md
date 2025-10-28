
















# Changelog

## 1.6.7 — 2025-10-28

- Python Orchestrator (debug/status/inspect) — fiabilité et observabilité renforcées, découpage en modules < 7 Ko.
  - Split du module debug en parties claires: api_debug.py (routeur), api_debug_stream.py (stream pas-à-pas), api_debug_inspect.py (inspect enrichi), api_debug_core.py (ACK robustes), api_debug_helpers.py (timeouts/DB tail/KV helpers).
  - Status/Inspect « jamais vides »: current_node/previous_node/next_node toujours exposés; fallback KV pour last_call/last_result_preview si aucun recent_steps.
  - ACK step/continue/run_until plus robuste: prise en compte des steps longs (ex: STEP_SLEEP) et extension auto du timeout minimal (~65s) pour garantir la pause.
  - Persistance d’IO minimale même hors debug (succès): call + last_result_preview (prévisualisés, sanitizés) injectés dans job_steps.details_json et KV; améliore observe/status/inspect.
  - Aucun changement de contrat d’API; pas de migration DB; rétro‑compatibilité préservée.
- Runner: factorisations internes sans changement fonctionnel.
  - Ajout runner_parts/config_merge.py et run_bootstrap.py (facilite maintenance/testing).

## 1.6.6 — 2025-10-27

- AO worker (Python orchestrator) conforme aux règles AST: suppression des conditionnels en steps, branchements via @cond, patterns tolérants; validate OK.
- README LLM dev workers enrichi (patterns sans if, checklist). Aucun breaking change.

## 1.6.5 — 2025-10-27

- Python Orchestrator — streaming reforgé (parité DB):
  - Observe (passif) refait: `/tools/py_orchestrator/observe` streame 1 chunk par step (INSERT `running`) + un chunk `updated: true` à chaque UPDATE (`succeeded`/`failed`). Contexte IO inclus (`io.in` = call, `io.out_preview`). Aucune interaction (pas de debug, pas de step/continue).
  - Nouveau endpoint: `/tools/py_orchestrator/start_observe` (start + observe en une requête), protocoles `sse|ndjson`, `timeout_sec` optionnel.
  - Debug streaming (actif) aligné sur la DB: tail insert+update, événements identiques à Observe; auto-step si debug en pause.
- Start propre: purge des vestiges `debug.step_trace` et `debug.trace` au démarrage d’un worker.
- Tool spec (`src/tool_specs/py_orchestrator.json`):
  - Distinction claire `debug` (actif) vs `observe` (passif) pour LLMs.
  - Schéma d’événements documenté (chunk_type, updated, io, phase…); timeouts précisés.
- Compatibilité: aucune migration DB; APIs rétro-compatibles. Le streaming reflète désormais strictement les logs `job_steps`.
