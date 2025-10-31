
# Dragonfly MCP Server

Ce serveur expose des endpoints MCP/Tools.

Changements récents
- Suppression complète du module /workers (API et UI associées).
- Nettoyage des références à l’ancienne UI.

Structure (extrait)
- src/server.py — Entrée Uvicorn
- src/app_factory.py — Création de l’app (inclut routes et outils)
- src/app_server/app_factory_compact.py — App FastAPI, montage static/assets, routes outils

Endpoints clés
- /tools, /execute, /debug, /config, /control (si présent)

Notes
- Les fichiers et scripts liés à “workers” ont été retirés.
