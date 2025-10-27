# Changelog

## 1.6.5 — 2025-10-27

- Python Orchestrator — streaming reforgé (parité DB):
  - Observe (passif) refait: `/tools/py_orchestrator/observe` streame 1 chunk par step (INSERT `running`) + un chunk `updated: true` à chaque UPDATE (`succeeded`/`failed`). Contexte IO inclus (`io.in` = call, `io.out_preview`). Aucune interaction (pas de debug, pas de step/continue).
  - Nouveau endpoint: `/tools/py_orchestrator/start_observe` (start + observe en une requête), protocoles `sse|ndjson`, `timeout_sec` optionnel.
  - Debug streaming (actif) aligné sur la DB: tail insert+update, évènements identiques à Observe; auto-step si debug en pause.
- Start propre: purge des vestiges `debug.step_trace` et `debug.trace` au démarrage d’un worker.
- Tool spec (`src/tool_specs/py_orchestrator.json`):
  - Distinction claire `debug` (actif) vs `observe` (passif) pour LLMs.
  - Schéma d’évènements documenté (chunk_type, updated, io, phase…); timeouts précisés.
- Compatibilité: aucune migration DB; APIs rétro-compatibles. Le streaming reflète désormais strictement les logs `job_steps`.
