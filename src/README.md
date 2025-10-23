




# 📁 src/ - Code Source Dragonfly MCP Server

Organisation modulaire du serveur MCP.

---

## 🏗️ Structure

```
src/
├── app_factory.py          # FastAPI app factory
├── server.py               # Entry point (uvicorn)
├── config.py               # Gestion .env
│
├── app_core/               # Modules core
│   ├── safe_json.py        # JSON sanitization
│   ├── tool_discovery.py   # Scan tools dynamique
│   └── workers/            # Module workers realtime
│       ├── __init__.py
│       ├── scanner.py      # Scan worker_*.db (2KB)
│       ├── config_builder.py  # Build config Realtime (DB→env)
│       └── db_query.py     # Query SQL read-only + validation
│
├── routes/                 # Routes FastAPI
│   └── workers.py          # /workers, /workers/{name}/realtime/*, /workers/{name}/query
│
├── tools/                  # 45+ tools MCP
│   ├── call_llm.py         # Appels LLM (local/distant)
│   ├── sqlite_db.py        # Base SQLite
│   ├── _mail_manager/      # Worker mail asynchrone (génère worker_*.db)
│   └── ...                 # Voir tools/README.md (auto-généré)
│
├── tool_specs/             # Specs JSON canoniques (source de vérité)
│   ├── call_llm.json
│   ├── sqlite_db.json
│   └── ...
│
├── templates/              # Templates HTML
│   ├── control/            # Control Panel (/control)
│   │   ├── index.py        # Assemble layout + sidebar + main
│   │   ├── layout.py       # Layout + CSS + (scripts JS inclus)
│   │   ├── sidebar.py      # Sidebar (logo, search, bouton config)
│   │   └── main.py         # Main view (status, container)
│   └── workers_page.py     # Page /workers/ui
│
├── static/                 # Assets frontend
│   ├── css/
│   │   └── workers.css     # Style workers
│   └── js/
│       ├── categories.js   # Catégories canoniques (Control)
│       ├── tools.js        # Chargement/rendu/exec des tools (Control)
│       ├── search.js       # Recherche texte (Control)
│       ├── config.js       # Modale config (Control)
│       └── main.js         # Initialisation + auto-reload (Control)
│
└── ui_html.py              # Deprecated shim vers templates/control (conservé)
```

---

## 🎤 Module Workers (Realtime)

- Audio & VAD client:
  - Coupure immédiate de la voix IA à la parole utilisateur et annulation de la réponse en cours.
  - Volume unique partagé sonnerie + IA (setVolume).
- Sonnerie:
  - Pattern “Skype-like” (~400/450 Hz), tu-tu-tuu tu-tu-tu, 2–10 s d’init.
  - Préchargement Mermaid pour overlay Process.
- Overlay Process (Mermaid):
  - Nœud courant surligné, timeline, “magnétophone” (⏮ ⏪ ▶︎/⏸ ⏩ ⏭).
  - KPIs dernière heure (Tâches, Appels call_llm, Cycles) recalculés à chaque refresh.
  - Incohérences logs ↔ schéma listées avec id + date/heure (exemples limités).

---

## 🔒 Sécurité

- SQL read-only strict (whitelist SELECT, blacklist mutations).
- Connexion SQLite en mode read-only (URI mode=ro).
- Masquage secrets pour /config.

---

## 🧪 Tests utiles

```
# Découverte des tools
python -c "from app_core.tool_discovery import discover_tools; discover_tools()"

# Scan workers
python -c "from app_core.workers import scan_workers; print(scan_workers())"

# Config realtime
python -c "from app_core.workers import build_realtime_config; print(build_realtime_config('alain'))"

# Query DB worker
python -c "from app_core.workers import query_worker_db; print(query_worker_db('alain', 'SELECT COUNT(*) FROM job_steps'))"
```

---

Made with 🐉 by Dragonfly
