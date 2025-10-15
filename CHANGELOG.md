# Changelog

## [1.27.3] - 2025-10-15

### ♟️ Nouveaux tools: Lichess (public) et Stockfish (Auto‑75)
- feat(lichess): tool public (sans token) avec endpoints clés:
  - Utilisateurs: profil, perfs, équipes, partie en cours, dernières parties (JSON, pgnInJson)
  - Équipes: détails, membres (limit + truncated)
  - Tournois: détails, résultats (limit + truncated)
  - Leaderboards: top par perfType (count ≤ 50)
  - Puzzles: quotidien, par id
- feat(stockfish_auto): évaluation/analyse avec auto‑profil (~75% CPU/RAM)
  - Auto Threads/Hash, presets quality (fast/balanced/deep), MultiPV=limit
  - Respect invariants (limit, counts, truncated). Implémentation moteur initiale branchée (UCI local requis)
- docs: specs JSON canoniques créées (src/tool_specs/lichess.json, src/tool_specs/stockfish_auto.json)

### ♟️ Mise à jour Stockfish (Auto‑75)
- BEHAVIOR: le moteur UCI local est désormais branché (plus un « stub »). Le binaire Stockfish doit être installé localement (ou `STOCKFISH_PATH` défini), sinon une erreur claire est retournée.
- FIX: timeout plancher ≥ 120s pour `go` (avec marge dynamique basée sur `movetime` et fenêtre de grâce 5s après `stop`) afin d’éviter les erreurs « Search did not finish before timeout » sur les presets balanced/deep et lors de l’usage de `searchmoves`.

### 🔒 Sécu & Perf
- Clients HTTP rate‑limited (Lichess: 200 ms défaut), pas de token exposé
- Orchestrations API/validators/core conformes au guide (parameters=object, additionalProperties=false)

---

## [1.27.2] - 2025-10-15

### 🧩 Workers Realtime — correctifs critiques, split <7KB, Mermaid durci, VU boost
- FIX Prompt & Tools
  - System prompt DB-first: worker_name, job, employeur, employe_depuis, persona, bio, tags, client_info, email, timezone, working_hours.
  - Envoi immédiat via `session.update` (+ fallback si `session.created` absent) → assistant contextuel fiable.
  - `session.update` inclut désormais `session.type: 'realtime'` (corrige l’erreur « Missing required parameter: 'session.type' »).
  - Tool `worker_query` réactivé par défaut (DB-first) et proxy sécurisé `/workers/{id}/tool/query`.
- FIX Mermaid
  - Sanitize des labels (quotes, backslashes, backticks, multi-formes) + rendu isolé dans `workers-process-render.js`.
  - Plus d’icône « bombe »; si erreur, fallback plain-text propre et log console explicite.
- UI/UX
  - VU ring nettement plus visible (échelle non‑linéaire, halo élargi, couleurs) + logs `[VU] amp`.
  - Transcript retiré des cartes (mini-widget unique). Transcript utilisateur non affiché.
  - `closeSession()` ferme proprement WS/micro/audio/ringback + reset VU.
- REFACTOR
  - Split `workers-session.js` en modules <7KB: `workers-session-state/core/ws/tools/audio`.
  - Suppression code mort: `workers-tools.js`.
  - Dédupe des fonctions d’appel (grid ↔ calls) et délégation claire.
- SEC & Robustesse
  - `/workers` n’expose plus `db_path` / `db_size`.
  - SQL LIMIT cap forcé (même si LIMIT présent) + indicateur `truncated`.

---

## [1.27.1] - 2025-10-15

### 🎙️ Workers Realtime — UI pro, process dynamique, VU ring réactif
- Split JS en modules maintenables (<7 Ko par feature):
  - workers-grid.js (cartes), workers-calls.js (appels), workers-status.js (stats & events), workers-gallery.js (galerie), workers-process.js (process Mermaid + replay), workers-vu.js (anneau VU)
- Process overlay (🧭) 100% DB-driven (zéro simulation):
  - Schéma Mermaid (job_state_kv.graph_mermaid), nœud courant surligné, arguments, historique (job_steps), replay ▶︎/⏸ 1x
  - Auto-refresh 10s du graph/état/historique pendant l’overlay
- Carte: « Derniers événements » (3 lignes, sans flood), stats, icônes premium et hover subtil
- Anneau VU réactif (couleur/scale) basé sur l’amplitude PCM16 des audios IA
  - Smoothing léger (EMA), scale 1→3, couleurs vert/jaune/rouge
- Polling:
  - Carte (stats + events): 5s (au lieu de 30s) pour un ressenti live
  - Overlay Process: refresh 10s
- Sécurité & robustesse:
  - Jamais de token renvoyé au frontend
  - Transcripts mini échappés (anti-XSS)
  - SQL corrigé (COALESCE finished_at, started_at)
  - Reset d’appel fiable (pas de faux « appel en cours »)

---

## [1.27.0] - 2025-10-14
- … (voir version précédente)
