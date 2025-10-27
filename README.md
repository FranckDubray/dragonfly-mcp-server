<p align="center">
  <img src="assets/logo.svg" alt="Dragonfly MCP Server" width="160" />
</p>

# Dragonfly MCP Server

Serveur MCP (Model Context Protocol) simple et robuste, avec ~59 tools prêts à l’emploi:
- Appels JSON unifiés via /execute
- UI web légère: Control Panel (tools) et Workers (realtime)
- Observabilité intégrée (SQLite, status, métriques)
- Outils variés: LLM, data, web/docs, intégrations, cartes, médias, e‑mail, Discord, chess, météo/astro…

Compatibilité MCP & Portail
- 100% compatible MCP (spec) avec extensions « addon » (superset MCP, jamais moins)
- Intégration prête pour le portail ai.dragonflygroup.fr

Liens rapides
- Control Panel: http://localhost:8000/control
- Workers: http://localhost:8000/workers
- Changelog: CHANGELOG.md
- Specs tools: src/tool_specs/*.json

---

## 🚀 Quickstart

```bash
# Installation
pip install -e .

# Configuration
cp .env.example .env
# Édite .env (clés API, endpoints, ports…)

# Lancer le serveur
./scripts/dev.sh        # Unix/Mac
./scripts/dev.ps1       # Windows
# ou
python src/server.py

# UIs
http://localhost:8000/control
http://localhost:8000/workers
```

---

## 🧰 Appeler un tool (/execute)

Chaque tool se consomme en JSON:
```json
{ "tool": "<tool_name>", "params": { ... } }
```

Exemples
- Date/heure:
```json
{ "tool": "date", "params": { "operation": "now", "format": "%Y-%m-%dT%H:%M:%S", "tz": "UTC" } }
```

- SQLite (SELECT):
```json
{ "tool": "sqlite_db", "params": { "operation": "query", "db": "example.db", "query": "SELECT 1 AS ok" } }
```

- LLM:
```json
{ "tool": "call_llm", "params": { "model": "gpt-4o-mini", "messages": [{ "role": "user", "content": "Hello" }] } }
```

Découvrir les tools
- UI: Control Panel (liste, recherche, formulaires)
- Specs: src/tool_specs/*.json (nom, description, schéma)

---

## 👀 Observation (workers)

- UI Workers: suivi en temps réel (exécutions, métriques).
- Streaming passif (SSE/NDJSON): 1 évènement par étape + 1 évènement “updated” en fin d’étape, avec contexte IO (appel + aperçu). L’observation n’altère pas l’exécution.

---

## 🧾 Stockage & Observabilité

- Base SQLite par worker: sqlite3/worker_<name>.db
  - journalisation des étapes (INSERT/UPDATE), état, métriques
- Status/métriques: affichés dans l’UI et via endpoints dédiés
- Logs HTTP/API: console + UIs

---

## 🗂️ Catégories de tools (exemples)

- Intelligence: call_llm, stockfish
- Données/IO: sqlite_db, json_ops, array_ops, template_map, date
- Web/Docs: universal_doc_scraper
- Intégrations: reddit_intelligence, chess_com, lichess, coingecko
- Cartes & géoloc: google_maps, device_location
- Média/traitement: ffmpeg_frames
- Météo/Aéronautique/Astro: aviation_weather, astronomy
- Communication: email_send, discord_webhook, discord_bot
- Utilitaires: sanitize_text, coerce_number, json_stringify, arithmetic

(Consulte la UI et src/tool_specs pour la liste complète.)

---

## 🧪 Bonnes pratiques

- Utiliser le Control Panel pour tester les tools rapidement (params validés).
- Renseigner .env pour activer les intégrations (API keys).
- Vérifier la DB worker en cas d’investigation (job_steps, métriques).

---

## 📦 Dev & scripts

- Endpoint unique: /execute (appel tools)
- Specs JSON par tool: src/tool_specs/*.json
- Scripts utilitaires: scripts/* (export, diagnostic…)

---

## 📝 Changelog

Voir CHANGELOG.md (versions et évolutions).
