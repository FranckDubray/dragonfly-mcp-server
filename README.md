# 🐉 Dragonfly MCP Server

**Serveur MCP (Model Context Protocol) moderne avec 45+ tools pour LLM, interface vocale temps réel et orchestration workers asynchrones.**

---

## 🚀 Quickstart

```bash
# Installation
pip install -e .

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# Démarrer le serveur (au choix)
./scripts/dev.sh          # Recommandé (Unix/Mac)
./scripts/dev.ps1         # Windows PowerShell
python src/server.py      # Direct

# Interfaces web (même serveur, port 8000)
http://localhost:8000/control     # Control Panel (tools)
http://localhost:8000/workers     # Workers Vocaux (NEW) ✨
```

---

## ✨ Fonctionnalités

### 🎙️ Workers Realtime (NEW v1.27.1)
Interface vocale temps réel pour interagir avec vos workers asynchrones :
- Session Realtime WebRTC: audio bidirectionnel, ringback, VAD et gating strict
- Processus dynamique (Mermaid): schéma, nœud courant, arguments, historique depuis la DB
- Replay ▶︎/⏸ du process (1x) — zéro simulation, 100% DB-driven
- Carte soignée: nom/métier/employeur, dispo locale, stats, “Derniers événements” (3 lignes), icônes premium (🧭, 📷, ✉️), galerie lightbox large
- Anneau VU réactif autour de l’avatar (amplitude PCM16): smoothing EMA, scale 1→3, vert/jaune/rouge

**Data requise (DB):**
- `job_state_kv.graph_mermaid`, `job_state_kv.current_node`, `job_state_kv.current_args` (optionnel)
- `job_steps` (name, status, started_at, finished_at)
- Carte: `avatar_url`, `job`, `employeur`, `employe_depuis`, `email` (optionnel), `tags_json` (optionnel), `gallery_json` (optionnel)

```sql
-- Mermaid
SELECT svalue FROM job_state_kv WHERE skey='graph_mermaid';
-- Nœud courant
SELECT svalue FROM job_state_kv WHERE skey IN ('current_node','current_step','current_stage');
-- Historique
SELECT name, status, COALESCE(finished_at, started_at) AS ts FROM job_steps ORDER BY id DESC LIMIT 3;
```

### 🔒 Sécurité
- Aucun token renvoyé au frontend (proxy backend → Portal)
- Transcripts mini échappés (HTML safe)
- Tool worker_query (SELECT only) via proxy backend

### 🧩 Modules JS découpés
- `workers-grid.js` (cartes), `workers-calls.js` (appels), `workers-status.js` (stats & events), `workers-gallery.js` (galerie), `workers-process.js` (process + replay), `workers-vu.js` (anneau VU), `workers-session.js` (orchestrateur)

---

## 📦 Architecture
- FastAPI (routes workers) + SafeJSON + tool registry
- SQLite local (`sqlite3/worker_*.db`), scan automatique
- Config Realtime hybride (DB-first, fallback .env)

---

## 🧪 Démo rapide
1. Ouvrez `http://localhost:8000/workers`.
2. Cliquez 📞 “Appeler” sur Alain → ringback → session.
3. Parlez: l’IA se coupe aussitôt; reprend après 1,4 s de silence.
4. Cliquez 🧭 “Processus” → schéma Mermaid réel, nœud courant, arguments, historique, replay.
5. Cliquez 📷 “Galerie” → lightbox large, navigation clavier.

---

## 📝 Changelog
Voir `CHANGELOG.md`.
