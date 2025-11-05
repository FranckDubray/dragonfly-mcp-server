# Changelog

## 1.6.11 — 2025-11-04

- **Python Orchestrator — SSE streaming fixes critiques**
  - Fix format SSE : ajout du préfixe `` manquant dans `tools_routes.py` (ligne 137).
  - Fix pollution par runs précédents : filtrage SQL strict par `run_id` (suppression des clauses `OR ?=''` dangereuses).
  - Protection startup : validation `run_id` non vide avant de démarrer un stream (observe/debug).
  - Détection restart : le stream s'arrête proprement avec message explicite si le worker redémarre (`worker_restarted`).
  - Fichiers corrigés : `api_observe.py`, `api_observe_stream.py`, `api_debug_stream.py`, `api_debug_helpers.py`.
  - HttpToolHandler (`http_tool.py`) : parsing SSE intégré pour consommer les flux côté orchestrator.
  - Spec tool nettoyé : `stream` documenté comme "réservé aux apps clientes" (pas pour LLM).
  - Doc complète : `docs/SSE_STREAMING.md` (format chunks, exemples JS/Python/cURL, bonnes pratiques).

- **Nouveau tool: Google Veo 3.1 Video (veo_video)**
  - Génération vidéo texte→vidéo via Google Veo 3.1 (modèles veo-3.1-generate-preview et veo-3.1-fast-generate-preview).
  - Operations: create (texte→vidéo), extend (extension de vidéos Veo), get_status, download, auto_start.
  - Orchestration: wait + auto_download (pattern Sora-like), polling adaptatif jusqu'à complétion.
  - Paramètres Veo 3.1: aspect_ratio (16:9, 9:16), resolution (720p, 1080p), seconds (4, 6, 8), person_generation, seed, negative_prompt.
  - Download: récupération via video.uri + HTTP (compatible SDK 1.48).
  - Storage: vidéos → docs/video; auto_start lance le player OS par défaut.
  - Image→vidéo temporairement désactivé (incompatibilité SDK 1.48, nécessite upgrade vers google-genai 0.6+).
  - Scripts de démarrage (dev.sh, dev.ps1) corrigés pour gérer les chemins avec espaces (space-safe).
  - Spec: src/tool_specs/veo_video.json conforme au guide (category: media, additionalProperties: false).

- **Nouveau tool: I18n files manager (i18n_manager)**
  - Un seul tool multi-actions pour gérer des fichiers i18n JSON et ES modules.
  - Opérations: list_langs, get_keys, upsert_keys (bulk), delete_keys (bulk), rename_key, upsert_key_all_langs (insertion d'une clé dans toutes les langues avec valeurs par langue + fallback).
  - Lecture/écriture robustes: parse ES module via json5, fallback regex pour __meta, écriture atomique + backups .bak.
  - Sécurité: chroot disque, whitelist extensions (.json, .js).
  - Conformité guide: limit/truncated/counts, additionalProperties:false, category: development, files <7KB, code découpé (api/core/utils/services/validators).

## 1.6.10 — 2025-10-31

- New tools: OpenAI Video (Sora) and Kling Video
  - openai_video (Sora):
    - Operations: create, get_status, download, list, delete, remix, auto_start.
    - Orchestration: wait + max_attempts + timeout_seconds (polling adaptatif), auto_download (vidéo), auto—thumbnail.
    - Storage: vidéos → docs/video; assets (thumbnail/spritesheet) → docs/images; pas de binaire inline.
    - Spec renforcée: size en enum (1280x720, 720x1280, 1792x1024, 1024x1792); input_reference_path (docs/images); erreurs toujours JSON (pas de 500/40X bruts).
  - kling_video (Kling):
    - Modes: text2video, image2video (incl. start/end via image_tail, uniquement kling—v2—1 Pro 5s/10s), multi_image2video (jusqu'à 4 images).
    - Masks: static_mask & dynamic_masks (kling—v1 uniquement, 5s), exclusifs avec image_tail et camera_control.
    - Prompt requis pour tous les modes; image locale en base64 sans préfixe ou URL.
    - Auth: JWT HS256 (KLING_ACCESS_KEY / KLING_SECRET_KEY), base: KLING_API_BASE (défaut: api—singapore).
    - Orchestration: wait + max_attempts + timeout_seconds; download vidéo → docs/video; thumbnail local via ffmpeg → docs/images; auto_start (ouvre avec le player OS).
    - List paginée (pageNum/pageSize); erreurs toujours JSON formatées.
- .env.example mis à jour: OPENAI_API_KEY/OPENAI_API_BASE, KLING_ACCESS_KEY/KLING_SECRET_KEY/KLING_API_BASE.
- Specs outillées: ajout masks à kling_video, clarification generation_mode; suppression des reliquats KLING_API_KEY; chemins unifiés (docs/video, docs/images).

## 1.6.9 — 2025-10-28

- Python Orchestrator — validate + preflight unifiés (zéro régression)
  - Nouveau cœur `validation_core.validate_full(worker_name, limit_steps=20, include_preflight, strict_tools, persist)` qui produit les issues compile—time (AST+structure) et les checks runtime (handlers/tools/réachabilité).
  - validate inclut désormais le preflight par défaut, sans effets de bord (KV) (`include_preflight=true`, `persist=false`). On peut revenir au comportement historique via `validate.include_preflight=false`.
  - preflight (au start) réutilise ce cœur avec `include_preflight=true` et `persist=true` pour persister `py.graph_warnings`/`py.graph_errors` et bloquer le run si erreurs.
  - Tool spec (validate) étendu: `include_preflight`, `strict_tools`, `persist` (optionnels, rétro—compatibles).

- Migrations (DB fraîche)
  - Suppression de `migrations.py` et du trigger; `begin_step` écrit `run_id` directement et crée l'indice composite `idx_job_steps_worker_runid` si besoin.

- Observabilité & métriques
  - Durée d'étape corrigée (`duration_ms = finished_at − started_at`).
  - Comptage LLM fiable sans dépendre du mode debug (agrégation KV depuis `usage`/`token_usage`).

- Refactor runner (< 7 KB par fichier): découpage core/inspect/usage pour maintenance.

- Nouveau tool: OBS Control (obs_control)
  - Contrôle OBS via obs—websocket v5 (scènes, items, inputs, médias, audio, filtres, transitions, sorties, studio, profils/collections, hotkeys, screenshots, snapshot/statut, service de stream) avec garde—fous.

- Compatibilité
  - Pas de migration DB requise; les nouvelles valeurs `duration_ms` s'appliquent aux étapes futures; LLM usage s'incrémente quand les outils renvoient un bloc `usage`.

## 1.6.8 — 2025-10-28

- Office to PDF Converter: stabilisé + mode headless (LibreOffice). Erreurs explicites, normalisation des réponses, validations durcies (anti—path traversal), README & spec mis à jour.

## 1.6.7 — 2025-10-28

- Python Orchestrator (debug/observe/status): refactor modulaire, ACK robustes, persistences IO même hors debug, streaming observe aligné DB; start purge des traces. Tool spec clarifié (debug vs observe).

## 1.6.6 — 2025-10-27

- AO worker (Python orchestrator) conforme aux règles AST; README patterns & checklist enrichi.

## 1.6.5 — 2025-10-27

- Streaming reforgé (observe + debug), purge traces au start, tool spec observe/stream mis à jour.
