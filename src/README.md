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
│   └── workers/            # Module workers realtime (NEW v1.27.0)
│       ├── __init__.py
│       ├── scanner.py      # Scan worker_*.db (2KB)
│       ├── config_builder.py  # Build config Realtime (5.7KB)
│       └── db_query.py     # Query SQL read-only + validation (3.6KB)
│
├── routes/                 # Routes FastAPI (NEW v1.27.0)
│   └── workers.py          # /workers, /workers/{name}/realtime/config, /workers/{name}/query
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
├── templates/              # Templates HTML (NEW v1.27.0)
│   └── workers_page.py     # Page /workers/ui
│
├── static/                 # Assets frontend
│   ├── css/
│   │   └── workers.css     # Style workers (10KB, design moderne)
│   └── js/
│       ├── main.js         # Control panel existant
│       ├── tools.js
│       ├── config.js
│       ├── workers-grid.js      # Grid workers (NEW)
│       ├── workers-vad.js       # VAD (NEW)
│       ├── workers-tools.js     # Tool execution (NEW)
│       ├── workers-session.js   # WebRTC session (NEW)
│       └── workers-graph.js     # Graph latence (NEW)
│
├── ui_html.py              # HTML control panel
└── ui_js.py                # JS control panel
```

---

## 🎤 Module Workers (NEW v1.27.0)

### `app_core/workers/`

Module dédié à l'interface vocale temps réel pour les workers asynchrones.

#### **scanner.py** (2KB)
- Scan `sqlite3/worker_*.db`
- Extrait metadata (worker_name, voice, persona)
- Retourne liste workers pour UI

```python
from app_core.workers import scan_workers

workers = scan_workers()  # [{"id": "alain", "name": "Alain", "voice": "ash", ...}]
```

#### **config_builder.py** (5.7KB)
- Charge persona + voice depuis `job_meta`
- Charge spec `sqlite_db` depuis `tool_specs/`
- Build instructions système (1ère personne, exemples requêtes)
- Retourne config complète pour session Realtime (wss_url, token, tools, turn_detection)

```python
from app_core.workers import build_realtime_config

config = build_realtime_config("alain")
# {
#   "worker_id": "alain",
#   "wss_url": "wss://...",
#   "token": "...",
#   "persona": "Je suis Alain...",
#   "instructions": "...",
#   "tools": [sqlite_tool],
#   "voice": "ash",
#   "turn_detection": {...}
# }
```

#### **db_query.py** (3.6KB)
- Exécution SQL read-only (`SELECT` uniquement)
- Validation stricte (whitelist/blacklist keywords)
- Formatting résultat pour TTS (texte court, prononçable)
- Timeout 5s, limit 200 rows max

```python
from app_core.workers import query_worker_db

result = query_worker_db("alain", "SELECT COUNT(*) FROM mail_classifications", limit=50)
# {
#   "success": True,
#   "rows": [{"COUNT(*)": 42}],
#   "count": 1,
#   "summary": "Résultat : 42"
# }
```

---

## 🛣️ Routes Workers

### `routes/workers.py` (3.3KB)

Endpoints FastAPI pour l'interface workers :

```python
from routes.workers import router

app.include_router(router)  # Prefix /workers
```

**Endpoints** :
- `GET /workers` : liste workers (scan sqlite3/)
- `GET /workers/{name}/realtime/config` : config session Realtime
- `POST /workers/{name}/query` : query SQL read-only
- `GET /workers/ui` : page HTML (template)

---

## 🎨 Frontend Workers

### **workers-grid.js** (4.9KB)
- Fetch `/workers` au chargement
- Render cards (avatar, nom, voix, stats)
- Rafraîchissement stats toutes les 30s
- Clic card → `openWorkerSession()`

### **workers-vad.js** (4.2KB)
- AudioContext + Analysers (user + AI)
- RMS computation (Uint8Array)
- Détection interruption (user parle pendant AI parle)
- Push activity timeline pour graph

### **workers-tools.js** (5.2KB)
- Buffering `function_call_arguments.delta` (streaming)
- Anti-duplicate (Set processedToolCalls)
- Exécution via `POST /execute` (tool sqlite_db)
- Formatting résultat pour TTS
- Indicator visuel (spinner)

### **workers-session.js** (10.4KB)
- WebRTC RTCPeerConnection + DataChannel
- Signaling vers AI Portal (wss://)
- `session.update` (voice, tools, turn_detection)
- Transcriptions (user + assistant)
- Latency tracking
- Controls (mute, hangup, enable audio)

### **workers-graph.js** (2.6KB)
- Canvas 2D graph latence
- Window glissante 60s
- Axes + grid + labels
- Plot points latence (ligne bleue)

### **workers.css** (10KB)
- Variables CSS (--primary, --success, --danger...)
- Grid workers (2 colonnes max, responsive)
- Cards hover effect
- Modal session (overlay + panel)
- Transcripts scrollable
- Responsive mobile (1 colonne)

---

## 🔧 Tool Discovery

### `app_core/tool_discovery.py`

Scan dynamique des tools :
- Pattern : `src/tools/<name>.py` (sans underscore)
- Chargement `spec()` depuis chaque tool
- Registry en mémoire (cache)
- Auto-reload optionnel (`AUTO_RELOAD_TOOLS=1` dans .env)

**Usage** :
```python
from app_core.tool_discovery import get_registry, discover_tools

discover_tools()  # Scan src/tools/
registry = get_registry()  # {tool_name: {name, spec, func, ...}}
```

---

## 📦 Tools

Voir `tools/README.md` (auto-généré depuis specs JSON).

**Règles** :
- Un fichier = un tool : `<tool_name>.py`
- Package implémentation : `_<tool_name>/` (avec underscore)
- Spec JSON canonique : `tool_specs/<tool_name>.json`
- Exports : `spec()` (charge JSON) + `run(**params)` (exécution)

**Exemple** :
```python
# src/tools/sqlite_db.py
import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.join(here, '..', 'tool_specs', 'sqlite_db.json')
    with open(spec_path, 'r') as f:
        return json.load(f)

def run(**params):
    from _sqlite_db.api import route_operation
    return route_operation(params)
```

---

## 🔒 Sécurité

### SQL Validation (`db_query.py`)
```python
FORBIDDEN_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
    'PRAGMA', 'ATTACH', 'DETACH', 'VACUUM', 'REPLACE'
]

def _validate_query(query):
    if not query.upper().startswith('SELECT'):
        raise ValueError("Only SELECT queries allowed")
    for kw in FORBIDDEN_KEYWORDS:
        if kw in query.upper():
            raise ValueError(f"Forbidden keyword: {kw}")
```

### Read-only DB
```python
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
```

---

## 📊 Monitoring

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("✅ Operation completed")
logger.warning("⚠️ Fallback used")
logger.error("❌ Execution failed")
```

### Metrics (Workers)
- Latency tracking (performance.now())
- VAD sampling (120ms interval)
- Graph window (60s glissant)
- Tool execution timing

---

## 🧪 Tests

```bash
# Test discovery
python -c "from app_core.tool_discovery import discover_tools; discover_tools()"

# Test worker scan
python -c "from app_core.workers import scan_workers; print(scan_workers())"

# Test config builder
python -c "from app_core.workers import build_realtime_config; print(build_realtime_config('alain'))"

# Test DB query
python -c "from app_core.workers import query_worker_db; print(query_worker_db('alain', 'SELECT COUNT(*) FROM mail_classifications'))"
```

---

## 📝 Contribution

**Audit obligatoire** après modif (voir `../LLM_DEV_GUIDE.md`) :
1. Tests préliminaires
2. Audit JSON spec + code
3. Correctifs
4. Tests validation
5. Tests non-régression
6. CHANGELOG
7. Commit + push

**Fichiers < 7KB** : découper si nécessaire (voir guide).

---

**Made with 🐉 by Dragonfly**
