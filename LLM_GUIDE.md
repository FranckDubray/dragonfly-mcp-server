# GUIDE POUR LLM — Dragonfly MCP Server

Ce document est destiné à un LLM (modèle) qui doit interagir avec ce projet en tant qu’« agent outillé ». Il résume comment découvrir les outils, les appeler proprement et quels comportements respecter.

—

## 1) Objectif du serveur
- Exposer des outils (Tools) via une API HTTP (FastAPI) compatible avec le format OpenAI tools.
- Découvrir automatiquement les tools présents dans `src/tools/`.
- Exécuter un tool à la demande via `POST /execute`.

—

## 2) Endpoints à utiliser
- GET `/tools`
  - Découvre les tools disponibles. La réponse inclut pour chaque tool: id, name, displayName, description et spec JSON.
  - Astuce: Ajoute `?reload=1` pour forcer un rescannage.

- POST `/execute`
  - Exécute un tool.
  - Corps attendu: `{ "tool": "<nom_du_tool>", "params": { ... } }`
  - Erreurs courantes: 404 (tool inconnu), 400 (mauvais paramètres), 504 (timeout).

- GET `/config` et POST `/config`
  - Lire/écrire les variables d’environnement utiles (tokens, endpoints).

—

## 3) Règles générales pour les Tools
- Chaque tool Python expose deux fonctions:
  - `run(**params) -> Any`
  - `spec() -> dict` (format OpenAI tools — function + parameters JSON Schema)
- Les schémas JSON doivent respecter:
  - `parameters.type` = `object` (ou bool), jamais un tableau.
  - Si un champ est `array`, il doit avoir `items`.
  - `additionalProperties: false` si on veut refuser les champs inattendus.

—

## 4) Outil clé: `call_llm`
- Orchestrateur de modèles LLM en 2 phases (streaming):
  1) Appel avec `tools` (stream) pour collecter d’éventuels `tool_calls` (puis exécution côté serveur)
  2) Appel sans `tools` (stream) pour produire le texte final
- Paramètres minimaux: `{ message: string, model: string }`. Options: `promptSystem`, `max_tokens`, `tool_names` (liste des tools MCP à exposer au LLM), `debug`.
- Usage cumulatif: la réponse `usage` additionne désormais les coûts/tokens des deux streams et de tous les appels imbriqués (y compris des `call_llm` enfants).
- Conseils d’orchestration pour un LLM:
  - Si tu as des tools MCP à ta disposition, demande `tool_names: ["nom_tool1", "nom_tool2", ...]` lors du premier appel de `call_llm`.
  - Ne produis pas de texte en dehors des `tool_calls` quand on te demande explicitement une délégation.
  - Évite les boucles infinies: une profondeur contrôlée (ex: A → B → sonar, puis stop).

—

## 5) Outil `script_executor`
- Exécute des scripts Python sandboxés pouvant orchestrer des tools MCP.
- Paramètres: `{ script: string, variables?: object, timeout?: integer, allowed_tools?: string[] }`.
- Important: `function.parameters` est un objet (jamais un tableau). Les arrays ont `items`.

—

## 6) JSON « sûr » et entiers géants
- Le serveur renvoie un JSON « safe »:
  - Les grands entiers peuvent être convertis en chaînes si la longueur dépasse un seuil (configurable).
  - `NaN`, `Infinity`, `-Infinity` sont rendus en chaînes littérales.
- Paramètres utiles:
  - `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`.

—

## 7) Où trouver quoi (carte du code)
- `src/server.py` — point d’entrée du serveur (Uvicorn), lit MCP_HOST/MCP_PORT
- `src/app_factory.py` — fabrique l’app FastAPI; endpoints; découverte/auto-reload des tools; sérialisation JSON sûre
- `src/config.py` — gestion `.env` (load/save), masquage des secrets
- `src/tools/` — tous les tools (un fichier par tool, plus des sous-packages dédiés)
  - `_call_llm/` — orchestrateur LLM (core, payloads, streaming, http_client, tools_exec, debug_utils)
  - `_math/` — modules mathématiques
  - `_script/` — sandbox du `script_executor`
- `src/tool_specs/` — specs JSON canonique de certains tools (ex: `call_llm.json`, `script_executor.json`)
- `src/README.md` — doc des endpoints et des fichiers côté serveur

—

## 8) Variables d’environnement essentielles pour les LLM
- `AI_PORTAL_TOKEN` — requis pour `call_llm`
- `LLM_ENDPOINT` — endpoint du service LLM (défaut fourni)
- `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `LLM_STREAM_TRACE`, `LLM_STREAM_DUMP`
- `MCP_URL` — URL du serveur MCP (utilisé par l’orchestrateur)

—

## 9) Bonnes pratiques pour un LLM
- Découvre d’abord les tools via `GET /tools`; respecte leurs schémas.
- Quand tu délègues via `call_llm`, évite d’ajouter du texte hors des tool_calls.
- Évite la récursion infinie; limite-toi à une profondeur prévue.
- Pour les arrays en spec: toujours définir `items`.
- Si un outil manque: remonte une erreur claire ou demande à l’utilisateur de l’activer.

—

## 10) Exemples minimalistes
- Exécuter une date:
  - POST `/execute` → `{ "tool": "date", "params": { "operation": "today" } }`
- Lancer `call_llm` simple:
  - POST `/execute` → `{ "tool": "call_llm", "params": { "message": "Dis bonjour", "model": "gpt-4o" } }`
- `script_executor` basique:
  - POST `/execute` → `{ "tool": "script_executor", "params": { "script": "print('hello'); result = 2+2" } }`

—

Pour plus de détails, lire également:
- [src/README.md](./src/README.md)
- Endpoint `/tools` pour la spec exacte des tools installés.
