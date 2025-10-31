# Changelog

## 1.6.10 — 2025-10-31

- New tools: OpenAI Video (Sora) and Kling Video
  - openai_video (Sora):
    - Operations: create, get_status, download, list, delete, remix, auto_start.
    - Orchestration: wait + max_attempts + timeout_seconds (polling adaptatif), auto_download (vidéo), auto‑thumbnail.
    - Storage: vidéos → docs/video; assets (thumbnail/spritesheet) → docs/images; pas de binaire inline.
    - Spec renforcée: size en enum (1280x720, 720x1280, 1792x1024, 1024x1792); input_reference_path (docs/images); erreurs toujours JSON (pas de 500/40X bruts).
  - kling_video (Kling):
    - Modes: text2video, image2video (incl. start/end via image_tail, uniquement kling‑v2‑1 Pro 5s/10s), multi_image2video (jusqu’à 4 images).
    - Masks: static_mask & dynamic_masks (kling‑v1 uniquement, 5s), exclusifs avec image_tail et camera_control.
    - Prompt requis pour tous les modes; image locale en base64 sans préfixe ou URL.
    - Auth: JWT HS256 (KLING_ACCESS_KEY / KLING_SECRET_KEY), base: KLING_API_BASE (défaut: api‑singapore).
    - Orchestration: wait + max_attempts + timeout_seconds; download vidéo → docs/video; thumbnail local via ffmpeg → docs/images; auto_start (ouvre avec le player OS).
    - List paginée (pageNum/pageSize); erreurs toujours JSON formatées.
- .env.example mis à jour: OPENAI_API_KEY/OPENAI_API_BASE, KLING_ACCESS_KEY/KLING_SECRET_KEY/KLING_API_BASE.
- Specs outillées: ajout masks à kling_video, clarification generation_mode; suppression des reliquats KLING_API_KEY; chemins unifiés (docs/video, docs/images).

## 1.6.9 — 2025-10-28

- Python Orchestrator — validate + preflight unifiés (zéro régression)
  - Nouveau cœur `validation_core.validate_full(worker_name, limit_steps=20, include_preflight, strict_tools, persist)` qui produit les issues compile‑time (AST+structure) et les checks runtime (handlers/tools/réachabilité).
  - validate inclut désormais le preflight par défaut, sans effets de bord (KV) (`include_preflight=true`, `persist=false`). On peut revenir au comportement historique via `validate.include_preflight=false`.
  - preflight (au start) réutilise ce cœur avec `include_preflight=true` et `persist=true` pour persister `py.graph_warnings`/`py.graph_errors` et bloquer le run si erreurs.
  - Tool spec (validate) étendu: `include_preflight`, `strict_tools`, `persist` (optionnels, rétro‑compatibles).

- Migrations (DB fraîche)
  - Suppression de `migrations.py` et du trigger; `begin_step` écrit `run_id` directement et crée l’indice composite `idx_job_steps_worker_runid` si besoin.

- Observabilité & métriques
  - Durée d’étape corrigée (`duration_ms = finished_at − started_at`).
  - Comptage LLM fiable sans dépendre du mode debug (agrégation KV depuis `usage`/`token_usage`).

- Refactor runner (< 7 KB par fichier): découpage core/inspect/usage pour maintenance.

- Nouveau tool: OBS Control (obs_control)
  - Contrôle OBS via obs‑websocket v5 (scènes, items, inputs, médias, audio, filtres, transitions, sorties, studio, profils/collections, hotkeys, screenshots, snapshot/statut, service de stream) avec garde‑fous.

- Compatibilité
  - Pas de migration DB requise; les nouvelles valeurs `duration_ms` s’appliquent aux étapes futures; LLM usage s’incrémente quand les outils renvoient un bloc `usage`.

## 1.6.8 — 2025-10-28

- Office to PDF Converter: stabilisé + mode headless (LibreOffice). Erreurs explicites, normalisation des réponses, validations durcies (anti‑path traversal), README & spec mis à jour.

## 1.6.7 — 2025-10-28

- Python Orchestrator (debug/observe/status): refactor modulaire, ACK robustes, persistences IO même hors debug, streaming observe aligné DB; start purge des traces. Tool spec clarifié (debug vs observe).

## 1.6.6 — 2025-10-27

- AO worker (Python orchestrator) conforme aux règles AST; README patterns & checklist enrichi.

## 1.6.5 — 2025-10-27

- Streaming reforgé (observe + debug), purge traces au start, tool spec observe/stream mis à jour.
