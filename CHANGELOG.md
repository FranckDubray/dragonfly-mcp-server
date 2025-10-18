# Changelog

## [1.28.0] - 2025-10-18

### 🚀 Orchestrator v1.0 — Production-Ready

**Generic JSON-driven FSM orchestrator for long-running workflows.**

#### ✨ Core Features
- **Tool MCP complet** : start/stop/status operations avec spawn runner détaché (OS-aware)
- **Engine FSM générique** : exécution de graph (START→nodes→END) sans logique métier
- **Context resolution** : `${...}` récursive (depth 10) pour worker_ctx et cycle_ctx
- **Handlers registry** : extensible (sleep interne, http_tool pour appels MCP)
- **Decisions** : truthy (falsy detection), enum_from_field (normalize, fallback)
- **Retry policies** : 3-level (transport, HTTP, node) avec expo backoff + Retry-After
- **Logging complet** : job_steps per node (UTC µs, details_json, ctx_diffs)
- **Security** : chroot workers/ strict, rejection .., symlinks, paths absolus

#### 📦 Architecture
- `src/tools/orchestrator.py` — Bootstrap MCP (467 B)
- `src/tools/_orchestrator/` — Package complet :
  - `api.py` — start/stop/status controller (10.5 KB)
  - `validators.py` — validation + chroot (2.6 KB)
  - `db.py` — SQLite helpers (2.9 KB)
  - `runner.py` — detached runner (7.1 KB)
  - `context/` — résolution ${...} + mapping outputs
  - `handlers/` — registry + http_tool MCP client + sleep
  - `logging/` — job_steps per node
  - `engine/` — orchestrator FSM + decisions
  - `policies/` — retry avec backoff
- `src/tool_specs/orchestrator.json` — Spec canonique (1.7 KB)
- `workers/` — Process JSON files (examples inclus)

#### 🧪 Tests
- ✅ 6/6 tests live via tool MCP (minimal, avancé, MCP tool, conflict, unknown, chroot)
- ✅ Workflow production validé : `production_briefing.process.json` (3 tools orchestrés : date, device_location, astronomy)
- ✅ Logging DB vérifié (job_steps complet, UTC µs timestamps)
- ✅ Retry policies testés (transport 3×, node-level expo backoff)
- ✅ Decisions testées (truthy, enum_from_field avec normalize/fallback)

#### 📖 Documentation
- **README complet** : `src/tools/_orchestrator/README.md` (12 KB)
  - Quick start, process structure, node types, context model, handlers, retry, logging, security, troubleshooting
- **Membank specs** : 10 fichiers techniques (orchestrator_tool_design, process_schema, contexts, logging, decisions, handlers, runner, error_handling, implementation, n8n_make_diff)
- **Examples** : 4 process files (test_minimal, test_advanced, test_mcp_tool, production_briefing)

#### 🎯 Use Cases
- Email triage automatique (fetch IMAP → classify LLM → move folders)
- Data pipelines (extract → transform → load)
- Monitoring & alerting (poll services → detect anomalies → send alerts)
- Content moderation (fetch content → classify → action)

#### 🔄 Workflow Production (Validé)
`workers/production_briefing.process.json` :
- ✅ 3 tools MCP orchestrés (date, device_location, astronomy)
- ✅ Decision truthy (validation data complète)
- ✅ Retry policies (2× per node, expo backoff)
- ✅ Context resolution `${cycle.data.location}`
- ✅ Logging complet (7 nodes, 683ms cycle time)
- ✅ Scopes déclaratifs (data, result)

#### 🔮 Roadmap v1.1 (Optionnel)
- Scope lifecycle hooks (enter/leave triggers)
- Hot-reload at runtime (process_uid check)
- Inspector tool (query logs, visualize graph)
- Circuit breaker (fail-fast)
- Transform handlers (sanitize_text, normalize_llm_output)

---

## [1.27.5] - 2025-10-15

### 🧩 Nouveaux tools
- Lichess (Public API, read‑only): profils, perfs, équipes, parties, tournois, leaderboards, puzzles (sans authentification).
- Stockfish (Auto‑75): évaluation de position et analyse de partie avec auto‑configuration (~75% des ressources), MultiPV, budget‑temps global (LLM 1 min par sonde typique).

### 📦 Divers
- Catalog/tools: specs chargées dans le registre (JSON canoniques disponibles sous src/tool_specs/).
- Docs: README racine mis à jour.

---

## [1.27.4] - 2025-10-15

### 🛠 Workers Realtime — Correctifs UI/UX & Mermaid (compléments)
- Time Machine:
  - Contrôles "magnétophone" (⏮ ⏪ ▶︎/⏸ ⏩ ⏭) pour rejouer pas‑à‑pas ou en auto.
  - Surlignage synchronisé: clic nœud Mermaid → sélection/scroll de l'étape dans la timeline; nœud courant surligné.
  - Timeline chargée jusqu'à 200 événements, ~15 lignes visibles (scroll dédié), horodatage FR (date+heure).
  - Alerte claire si incohérence logs ↔ schéma (nœuds inconnus) avec détails (id + date/heure), échantillons limités.
  - Cache du code Mermaid pendant le replay (perf): plus de requêtes DB par step.
- Galerie/Lightbox:
  - Galerie fermée par défaut; ouverture/fermeture via l'icône seulement.
  - Scroll horizontal accéléré dans la galerie; lightbox uniquement pour vignettes/data‑full (jamais l'avatar).
- VU Ring:
  - Anneau vert/jaune/rouge plus visible, lissage EMA + boost non linéaire, compat APIs legacy.
- CSS/Thème:
  - Thème clair confirmé; avatar 64×64 rond, recadrage; timeline ~15 lignes visibles.
- Prompt système / Contexte:
  - DB complétée (timezone, working_hours, bio) puis nettoyage (email/tags retirés) conformément aux demandes.

### 🔔 Sonnerie & Audio
- Sonnerie "Skype-like" par défaut (≈400/450 Hz), cadence tu‑tu‑tuu tu‑tu‑tu, agréable et familière pour 2–10 s.
- Volume par défaut 50% et curseur unique pilotant à la fois la sonnerie et la voix IA (setVolume partagé).
- Préchargement de Mermaid au chargement de page (/workers) pour supprimer la latence (fallback + retry garantis côté JS si CDN lent).

### 🧠 VAD & Interruption IA
- Détection rapide: dès que l'utilisateur parle, arrêt immédiat du haut-parleur IA et cancel de la réponse courante.
- Reprise rapide au silence stable; option d'accentuation (<200ms) possible.

### 📊 KPIs Process (overlay)
- Nouveau panneau "Activité (dernière heure)" dans l'overlay Process: 
  - Tâches (succeeded/failed), Appels call_llm, Cycles (sleep_interval ou fallback finish_mailbox_db)
  - Recalcul à chaque refresh (10 s) pendant l'overlay.

### 🎨 Couleur cartes selon activité (1h)
- 0–15 → vert, 16–40 → orange, >40 → rouge (classes activity-*)

### 🐛 Corrections Mermaid
- Chargeur Mermaid robuste (retry) + fallback "Diagramme indisponible" avec message explicite.
- Normalisation du source Mermaid (quotes, backslashes) + surlignage du nœud courant.

### 🗄 Données & Seeds de test
- Injection de cycles cohérents (nomail + mail occasionnels), durées réalistes: sleep 10 min, LLM 1 min, enchaînement strict des nœuds.
- Lot par ~50 lignes, répété pour couvrir une plage temporelle jusqu'à atteindre des tests denses.

---
