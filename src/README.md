# Dragonfly MCP Server — Dossier `src/`

Ce répertoire contient le code du serveur MCP (FastAPI) et des outils.
Vous trouverez ci‑dessous:
- les endpoints HTTP exposés par l’API
- le rôle des fichiers principaux
- un bref guide d’exécution et de configuration

---

## Endpoints HTTP

- GET /tools
  - Retourne la liste des tools découverts, avec un identifiant, un nom, un displayName, une description et la spec JSON (format OpenAI tools). Côté serveur, les fonctions Python ne sont pas retournées.
  - Auto‑reload: si AUTO_RELOAD_TOOLS=1, le serveur redétecte automatiquement les nouveaux fichiers dans `src/tools/`.
  - Caching: ETag sur la charge utile; support du 304 lorsqu’If-None-Match correspond.

- POST /execute
  - Exécute un tool. Corps JSON: { tool: string | tool_reg, params: object }.
  - Timeout par défaut: EXECUTE_TIMEOUT_SEC.
  - Paramètres invalides → 400; tool inconnu → 404; timeout → 504.
  - La réponse est sérialisée via SafeJSONResponse (voir ci‑dessous), incluant la sanitation des grands entiers et des valeurs non‑finies.

- POST /debug
  - Écho/debug: journalise le body brut, le JSON parsé et tente de construire un ExecuteRequest. Pratique pour diagnostiquer la forme des requêtes envoyées par un client.

- GET /config
  - Retourne l’état des principales variables (masquées si sensibles): GITHUB_TOKEN, AI_PORTAL_TOKEN, LLM_ENDPOINT, chemin du fichier .env.

- POST /config
  - Met à jour/sauvegarde des variables d’environnement dans `.env` (persistées; `.gitignore` est mis à jour côté projet).

- GET /control
  - Sert un panneau de contrôle HTML pour interagir avec le serveur (configurer les tokens, tester les tools, etc.).

- GET /control.js
  - Sert le JavaScript utilisé par le panneau de contrôle.

---

## Comportements et mécanismes clefs

- Découverte automatique des tools
  - Le package `tools` est parcouru (sous‑modules et sous‑packages, hors noms commençant par `_`).
  - Un module est enregistré comme tool s’il expose deux callables: `run()` et `spec()`.
  - Le `spec()` retourne une spec conforme au format "function" d’OpenAI tools (ou fallback minimal si la spec JSON dédiée n’est pas disponible).

- Auto‑reload des tools
  - Si `AUTO_RELOAD_TOOLS=1`, le serveur compare l’mtime/ensemble des fichiers de `src/tools/` et relance la découverte quand une modification est détectée.
  - Forçage manuel: ajouter `?reload=1` à l’URL (GET /tools) ou activer `RELOAD=1`.

- Safe JSON / grands entiers
  - `SafeJSONResponse` + `sanitize_for_json()` convertissent automatiquement:
    - grands entiers en chaînes si leur nombre de chiffres dépasse `BIGINT_STR_THRESHOLD` (activable via `BIGINT_AS_STRING`)
    - `NaN`, `Infinity`, `-Infinity` en chaînes littérales
  - `PY_INT_MAX_STR_DIGITS` peut être levé pour supporter la conversion en chaîne d’entiers très grands (factoriels, etc.).

- Timeout et exécution des tools
  - `asyncio.wait_for()` avec pool d’exécuteur (thread). Timeout réglé par `EXECUTE_TIMEOUT_SEC`.

---

## Fichiers principaux

- server.py
  - Point d’entrée (module exécutable). Lit MCP_HOST/MCP_PORT et démarre Uvicorn avec l’app FastAPI créée par `create_app()`.

- app_factory.py
  - Fabrique l’application FastAPI: endpoints, middleware CORS, handlers d’erreurs, découverte des tools, auto‑reload, SafeJSONResponse.
  - Composants notables:
    - `discover_tools()` : scan du package `tools`, import/reload des modules, enregistrement dans le registre interne.
    - `should_reload()` : logique d’auto‑reload basée sur mtime et set de fichiers.
    - `sanitize_for_json()` / `SafeJSONResponse` : sérialisation robuste.

- config.py
  - Chargement/sauvegarde des variables d’environnement (.env), masquage des secrets, localisation de la racine du projet.

- ui_html.py / ui_js.py
  - HTML/JS du panneau de contrôle (/control et /control.js).

- tools/ (package)
  - Contient les implémentations des tools. Chaque tool expose:
    - `run(**params) -> Any`
    - `spec() -> dict` (spécification OpenAI tools)
  - Exemples inclus: `call_llm`, `math`, `date`, `git`, `gitbook`, `sqlite_db`, `pdf_search`, `pdf2text`, `reddit_intelligence`, `script_executor`, `universal_doc_scraper`.
  - Sous‑packages spécialisés:
    - `_call_llm/` : orchestrateur LLM en deux phases (stream). Fichiers clés:
      - `core.py` : logique principale (depuis 2025‑09, agrégation de l’usage cumulative à travers les phases et appels imbriqués)
      - `payloads.py`, `http_client.py`, `streaming.py`, `tools_exec.py`, `debug_utils.py`
    - `_math/` : sous‑modules pour arithmétique, symbolique, proba, algèbre linéaire, HP, etc.
    - `_ffmpeg/` : détection de plans (native PyAV), extraction d’images; debug par frame (similarité%), exec_time_sec
    - `_script/` : exécution sandbox (ScriptExecutor)

- tool_specs/
  - Spécifications JSON canoniques pour certains tools (ex: `call_llm.json`, `script_executor.json`, `ffmpeg_frames.json`). Le code Python peut utiliser un fallback minimal si le JSON n’est pas disponible.

---

## Variables d’environnement utiles

- Réseau/serveur: MCP_HOST, MCP_PORT, LOG_LEVEL
- Exécution: EXECUTE_TIMEOUT_SEC, AUTO_RELOAD_TOOLS, RELOAD
- JSON/entiers: BIGINT_AS_STRING, BIGINT_STR_THRESHOLD, PY_INT_MAX_STR_DIGITS
- LLM: AI_PORTAL_TOKEN, LLM_ENDPOINT, LLM_REQUEST_TIMEOUT_SEC, LLM_RETURN_DEBUG, LLM_STREAM_TRACE, LLM_STREAM_DUMP
- Divers: GITHUB_TOKEN

---

## Exemples d’appels

- Lister les tools
  - curl "http://127.0.0.1:8000/tools"

- Exécuter un tool
  - curl -X POST "http://127.0.0.1:8000/execute" \
    -H "Content-Type: application/json" \
    -d '{"tool":"date","params":{"operation":"today"}}'

- Déboguer une requête
  - curl -X POST "http://127.0.0.1:8000/debug" \
    -H "Content-Type: application/json" \
    -d '{"tool":"math","params":{"operation":"factorial","n":10}}'

---

## Développement rapide

- Lancer en local
  - `python -m server` (ou via scripts fournis)

- Ajouter un tool
  - Créez `src/tools/<tool_name>.py` avec `run()` et `spec()`.
  - Optionnel: ajoutez `src/tool_specs/<tool_name>.json`.
  - Si `AUTO_RELOAD_TOOLS=1`, le nouveau tool sera détecté automatiquement.

---

Pour plus de détails, voir aussi le README racine du projet.
