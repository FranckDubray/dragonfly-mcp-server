# Dragonfly MCP Server

Serveur MCP multi-outils (FastAPI) avec auto-découverte des tools et panneau de contrôle web.

## Fonctionnalités
- Outils inclus: Git/GitHub, SQLite, PDF, Date/Heure, Math (haute précision), LLM Orchestrator
- Auto-reload des tools (détection automatique des nouveaux fichiers sous `src/tools/`)
- JSON sûr (valeurs NaN/Infinity sanitizées)
- Panneau de contrôle web (`/control`) pour configurer les tokens et tester

## Outils MCP disponibles (src/tools)
- call_llm: Orchestrateur LLM + tools (2 appels, tool_choice=required puis none)
- math: calcul numérique/HP et symbolique (modules dans `src/tools/_math/`)
- date: opérations date/heure (now/today, diff, add, format, parse, weekday, week_number)
- git: GitHub API + Git local (chroot, opérations limitées)
- gitbook: découverte/contenu/sitemap GitBook
- sqlite_db: SQLite chrootée dans `<projet>/sqlite3` (noms de DB validés)
- pdf_search: recherche de mots-clés dans les PDF
- pdf2text: extraction de texte depuis PDF
- reddit_intelligence: recherche multi, experts, tendances, sentiment
- script_executor: exécution encadrée de scripts (sécurité/_script)
- universal_doc_scraper: détection/scraping universel de docs
- academic_research_super: outil agrégateur pour recherches avancées

Les spécifications JSON (OpenAI tools) correspondantes se trouvent dans `src/tool_specs/` (items obligatoires pour les arrays).

## Prérequis
- Python 3.9+
- Accès Internet si vous utilisez les APIs (GitHub, LLM)

## Installation (développement)
```bash
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
ycd dragonfly-mcp-server
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

## Lancer le serveur
- Linux/macOS: `./scripts/dev.sh`
- Windows: `scripts\dev.ps1`

Le serveur démarre par défaut sur `http://127.0.0.1:8000`.

## Configuration
Vous pouvez configurer via variables d'environnement ou via l'interface web (recommandé):
- Ouvrez `http://HOST:PORT/control` (panneau de contrôle)
- Onglet "Config" → saisissez/mettez à jour les tokens
- Les valeurs sont persistées dans `.env` (automatiquement ajoutée à `.gitignore`)

Variables principales:
- MCP_HOST: hôte du serveur (défaut `127.0.0.1`)
- MCP_PORT: port du serveur (défaut `8000`)
- LOG_LEVEL: niveau de logs (`DEBUG`/`INFO`/`WARN`/`ERROR`)
- EXECUTE_TIMEOUT_SEC: timeout d'exécution des tools (défaut `30`)
- AUTO_RELOAD_TOOLS: `1` pour auto-détecter les nouveaux tools
- AI_PORTAL_TOKEN: token LLM (pour l'outil `call_llm`)
- LLM_ENDPOINT: URL du service LLM (défaut `https://dev-ai.dragonflygroup.fr/api/v1/chat/completions`)
- LLM_DEBUG: `1/true/yes/on/debug` pour logs détaillés de l'orchestrateur
- GITHUB_TOKEN: token GitHub (scopes `repo`) pour l'outil `git`

## Endpoints utiles
- `GET /tools`: liste des tools et leurs specs
- `POST /execute`: exécuter un tool
- `GET /control`: panneau de contrôle web
- `GET/POST /config`: lecture/écriture de la configuration JSON

## Ajouter un tool
- Créez `src/tools/mon_tool.py` avec `run()` et `spec()`
- Optionnel: spec JSON `src/tool_specs/mon_tool.json` (OpenAI schema; `array` → `items` obligatoire)
- Le serveur détecte automatiquement le nouveau fichier si `AUTO_RELOAD_TOOLS=1`

## Sécurité
- SQLite: bases sous `<projet>/sqlite3` (noms stricts validés)
- Git local: opérations locales limitées à la racine du projet
- Pas d'accès disque hors répertoires prévus

## Math haute précision
- `mpmath` utilisé lorsque `precision > 16`
- Si `mpmath` absent et `precision > 16` → erreur explicite (pas de fallback silencieux)

## Dépannage
- Streaming LLM vide: vérifier SSE "data: "; fallback non-stream
- LLM qui ignore les tools: 1er appel `tool_choice=required`; 2e appel `tool_choice=none` sans `tools`
- Specs JSON invalides: les `array` doivent avoir `items`

## Scripts
- `scripts/dev.sh` (Linux/macOS) et `scripts/dev.ps1` (Windows) démarrent via `python -m server`

Licence: MIT
