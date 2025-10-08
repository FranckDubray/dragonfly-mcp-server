


<div align="center">

<!-- Local logo for reliability (placed in assets/) -->
<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. Découverte automatique des tools, exécution sécurisée, orchestrateur LLM avancé, et panneau de contrôle web.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688)
![Status](https://img.shields.io/badge/Status-Active-success)

</div>

---

## ✨ Vue d’ensemble
Dragonfly MCP Server expose des « tools » (au format OpenAI tools) via des endpoints HTTP simples:
- Découverte automatique des outils sous `src/tools/`
- Exécution d’un tool via `POST /execute`
- Orchestration LLM en 2 phases via `call_llm` (avec usage cumulatif)
- Panneau de contrôle web pour configurer et tester (`/control`)

> Pour les détails d’API (endpoints, sérialisation JSON, etc.), consultez aussi [src/README.md](./src/README.md).

---

## 📚 Sommaire
- [Fonctionnalités](#-fonctionnalités)
- [Demo rapide](#-demo-rapide)
- [Installation](#-installation)
- [Démarrage](#-démarrage)
- [Prerequis Python](#-prerequis-python)
- [Endpoints](#-endpoints)
- [Outils inclus](#-outils-inclus)
- [Orchestrateur LLM (call_llm)](#-orchestrateur-llm-call_llm)
- [Configuration](#-configuration)
- [Sécurité](#-sécurité)
- [Structure du projet](#-structure-du-projet)
- [Migration notes](#-migration-notes)
- [Pour les LLM « développeurs »](#-pour-les-llm-développeurs)
- [Feuille de route](#-feuille-de-route)
- [Licence](#-licence)

---

## 🚀 Fonctionnalités
- Auto‑reload des tools (détection de nouveaux fichiers dans `src/tools/`)
- JSON « sûr »: grands entiers, NaN/Infinity sanitisés
- Orchestration LLM streaming en 2 phases (avec cumul d’usage multi‑niveaux)
- Panneau de contrôle web (`/control`)
- Outils prêts à l’emploi: Git/GitHub, SQLite, PDF, Date/Heure, Math (HP), GitBook, Reddit, Universal Doc Scraper, Script Executor, FFmpeg frames, Academic Research, etc.

---

## ⚡ Demo rapide
Exécuter un tool en une requête:

```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{"tool":"date","params":{"operation":"today"}}'
```

Orchestrer un LLM (réponse texte) :

```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"call_llm",
   "params":{ "message":"Dis bonjour en français.", "model":"gpt-4o" }
 }'
```

Lister les tools disponibles:

```bash
curl -s http://127.0.0.1:8000/tools
```

---

## 🛠 Installation
Prérequis: Python 3.11 ou 3.12. Vérifiez avec: `python3 --version`. Si votre version est < 3.11, installez via pyenv/conda ou depuis python.org.

```bash
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
cd dragonfly-mcp-server
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

## ▶️ Démarrage
- Linux/macOS: `./scripts/dev.sh`
- Windows: `scripts\dev.ps1`

Par défaut: http://127.0.0.1:8000

Panneau de contrôle: http://127.0.0.1:8000/control

---

## 🐍 Prerequis Python
- Version minimale recommandée: Python 3.11 ou 3.12.
- Le projet utilise des fonctionnalités modernes (annotations/typing, comportement de json/ints, etc.) pouvant échouer avec des versions trop anciennes.
- Les scripts de démarrage vérifient automatiquement la version installée et abortent si la version est trop ancienne.

> Astuce: utilisez pyenv pour installer la bonne version, ou conda/mamba.

---

## 🔗 Endpoints
- `GET /tools` — liste des tools (spec incluse). Ajouter `?reload=1` pour forcer un rescannage.
- `POST /execute` — exécuter un tool: `{ tool: string, params: object }`
- `GET /config` / `POST /config` — lire/écrire la configuration (.env)
- `GET /control` — panneau HTML
- `GET /control.js` — script du panneau

Détails étendus: [src/README.md](./src/README.md)

---

## 🧪 Outils inclus
- `call_llm`: orchestrateur LLM (2 phases, usage cumulatif)
- `math`: calcul numérique/HP, symbolique, algèbre linéaire (+ extensions), solveurs, séries, nombres premiers, sommes
- `date`: now/today, diff, add, format, parse, weekday, week_number
- `git`: GitHub API + Git local (opérations sécurisées)
- `gitbook`: discovery/lecture/search GitBook
- `sqlite_db`: SQLite chroot (bases sous `<projet>/sqlite3`)
- `pdf_search` / `pdf2text`
- `reddit_intelligence`
- `universal_doc_scraper`
- `script_executor`: exécution de scripts Python sandboxés orchestrant des tools
- `ffmpeg_frames`: extraction d’images/frames d’une vidéo via FFmpeg (détection native PyAV, debug de similarité, exec_time_sec)
- `academic_research_super`: pipeline avancé de recherche académique (agrégation, scraping, synthèse)

Specs JSON (OpenAI tools) correspondantes dans `src/tool_specs/`.

---

## 🧠 Orchestrateur LLM (`call_llm`)
- 1er stream (avec tools): collecte des `tool_calls`, exécution côté serveur
- 2e stream (sans tools): génération du texte final
- Usage cumulatif: additionne automatiquement les usages des 2 streams et de tous les appels imbriqués (ex: A → B → sonar)
- Paramètres clés: `message`, `model`, `tool_names` (liste des tools exposés au modèle), `promptSystem`, `debug`

---

## ⚙️ Configuration
Variables principales:
- Réseau/serveur: `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`
- Exécution: `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`, `RELOAD`
- LLM: `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `MCP_URL`
- JSON/entiers: `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`
- Divers: `GITHUB_TOKEN`

Configurer via `/control` (recommandé) ou via `.env`.

---

## 🔒 Sécurité
- SQLite chroot: DBs sous `<projet>/sqlite3` (noms validés)
- Git local: opérations limitées à la racine du projet
- `script_executor`: sandbox stricte (pas d’accès non autorisé)
- Safe JSON: sérialisation robuste (NaN/Infinity, très grands entiers)

---

## 🗂 Structure du projet
```
src/
  app_factory.py     # FastAPI app, endpoints, auto-reload, Safe JSON
  server.py          # Entrée (Uvicorn) — crée l’app et lance le serveur
  config.py          # .env (load/save), masquage des secrets
  tools/             # Tous les tools (run() + spec())
    _call_llm/       # Orchestrateur LLM: core, payloads, streaming, http_client...
    _math/           # Arithmétique, symbolique, proba, algèbre linéaire, etc.
    _ffmpeg/         # Utilitaires FFmpeg (frames, conversion)
    _script/         # Sandbox du ScriptExecutor
  tool_specs/        # Specs JSON canoniques (OpenAI tools)
  README.md          # Doc API interne (endpoints + composants)
```

---

## 🧭 Migration notes
- Python 3.11+ requis (scripts et metadata l’imposent).
- Les scripts de dev chargent maintenant `.env` avant l’install et le lancement.
- Le dossier top-level `script_executor/` est ignoré par Git: déplacez vos scripts utilisateurs dans un dossier hors repo si besoin.
- Pour les fonctionnalités math avancées, installez `sympy`; pour haute précision, `mpmath` (optionnel).

---

## 👩‍💻 Pour les LLM « développeurs »
Vous modifiez/étendez le dépôt ? Lisez ce guide:
- [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)
  - Conventions, invariants, checklists, pièges à éviter
  - Règles de spec JSON (parameters = object, arrays → items)
  - Détails sur `call_llm` (streaming, usage cumulatif) et le JSON sûr

---

## 🗺️ Feuille de route (extraits)
- [ ] Tests automatisés (tools + orchestrateur)
- [ ] Exemples interactifs dans `/control`
- [ ] Intégration d’auth facultative sur les endpoints sensibles
- [ ] Export de métriques (Prometheus)

Contributions bienvenues — issues & PRs !

---

## 📄 Licence
MIT — voir [LICENSE](./LICENSE)
