# LLM DEV GUIDE — Dragonfly MCP Server

Ce guide s’adresse à un LLM « développeur » qui doit modifier/étendre ce dépôt. Il résume la structure, les conventions, les invariants, les pièges à éviter, et des checklists de validation.

---

## 1) Objectif et architecture
- Projet: serveur MCP (FastAPI) exposant des outils (« tools ») au format OpenAI tools.
- Découverte dynamique des tools dans `src/tools/` (chaque outil = module Python avec `run()` et `spec()`).
- Endpoints principaux: `GET /tools`, `POST /execute`, `GET/POST /config`, `GET /control`, `GET /control.js`.
- Réponses JSON « sûres »: grands entiers, NaN/Infinity sont gérés pour ne pas casser les clients.

---

## 2) Carte rapide du code
- `src/server.py` — point d’entrée (Uvicorn). Ne pas dupliquer la logique métier ici.
- `src/app_factory.py` — crée l’app FastAPI, endpoints, CORS, handlers, découverte des tools, auto‑reload, JSON sûr.
- `src/config.py` — gestion `.env` (load/save), masquage des secrets, racine projet.
- `src/tools/` — tools (un fichier par outil) + sous‑packages spécialisés:
  - `_call_llm/` — orchestrateur LLM (streaming) → voir core/payloads/http_client/streaming/tools_exec/debug_utils.
  - `_math/` — calcul numérique/HP/symbolique.
  - `_script/` — exécution sandbox pour `script_executor`.
- `src/tool_specs/` — specs JSON canoniques de certains tools.
- `src/README.md` — endpoints + fichiers clés (doc API côté serveur).
- `LLM_GUIDE.md` — guide d’« utilisation outillée » pour un LLM agent consommateur (non‑dev).

---

## 3) Conventions et invariants (à respecter)
- Python ≥ 3.9, privilégier les annotations de type.
- Un tool doit fournir:
  - `run(**params) -> Any`
  - `spec() -> dict` « type=function » conforme OpenAI tools.
- Spécifications JSON (très important):
  - `function.parameters` doit être un objet (ou bool), JAMAIS un tableau.
  - Tout champ `array` doit avoir `items`.
  - Quand pertinent, mettre `additionalProperties: false`.
- Découverte des tools: `discover_tools()` recharge/import; n’utilisez pas de side‑effects globaux non idempotents à l’import.
- Sécurité: ne pas affaiblir la sandbox de `script_executor`; pas d’accès disque hors répertoires prévus; respecter la chroot SQLite.
- Performance: ne bloquez pas l’event loop; le travail CPU se fait via exécuteur (thread) déjà géré dans `/execute`.

---

## 4) Orchestrateur `call_llm` (développement)
- Deux appels streaming:
  1) Avec `tools`: on collecte `tool_calls` et exécute les MCP tools côté serveur.
  2) Sans `tools`: production du texte final.
- Usage cumulatif (implémenté):
  - Somme les usages (tokens/coûts) du 1er stream, des outils exécutés (incl. `call_llm` enfants), et du 2e stream.
  - Merge: addition pour nombres, copie pour non‑numériques; ne pas sommer les clés contenant `price`.
- Debug contrôlé par env/param (`LLM_RETURN_DEBUG` ou `debug=True`): expose payloads synthétiques, SSE previews, usage_breakdown.
- Streaming/SSE: `streaming.py` gère l’agrégation de texte et la reconstruction de `tool_calls` (OpenAI + variantes provider‑spécifiques + legacy function_call).
- Pièges:
  - Éviter récursion infinie (prévoir profondeur max côté prompts/flows).
  - Respecter strictement les schémas des tools exposés au modèle (via `tool_names`).

---

## 5) Safe JSON & grands entiers
- `sanitize_for_json()` + `SafeJSONResponse` dans `app_factory.py`:
  - Convertit en chaîne les entiers géants au‑delà de `BIGINT_STR_THRESHOLD` (si `BIGINT_AS_STRING=1`).
  - Rend `NaN`, `Infinity`, `-Infinity` en chaînes.
  - Lève la limite Python 3.11+ d’int→str si `PY_INT_MAX_STR_DIGITS` est paramétré.
- À respecter: n’introduisez pas de sérialisation custom qui contourne cette hygiène.

---

## 6) Endpoints et flux de dev
- Démarrer localement: `./scripts/dev.sh` (ou `scripts/dev.ps1` sur Windows) → démarre `python -m server`.
- Rafraîchir les tools: `GET /tools?reload=1`.
- Exécuter un tool: `POST /execute` avec `{ "tool": "<nom>", "params": { ... } }`.
- Voir/éditer config: `GET/POST /config`.

---

## 7) Ajouter/Modifier un tool
- Créer `src/tools/mon_tool.py` avec `run()` et `spec()`.
- (Optionnel) `src/tool_specs/mon_tool.json` si vous voulez une spec canonique.
- Vérifier:
  - `GET /tools?reload=1` → le tool apparaît, la spec est valide (params=object, arrays→items).
  - `POST /execute` avec paramètres de test.
- Pour `script_executor`: ne jamais rendre `function.parameters` en tableau; arrays doivent avoir `items`.

---

## 8) Tests manuels rapides
- `date.today`
  - POST `/execute` → `{ "tool": "date", "params": { "operation": "today" } }`
- `call_llm` simple (ne délègue pas):
  - `{ "tool": "call_llm", "params": { "message": "Bonjour", "model": "gpt-4o" } }`
- `call_llm` chaîné (A→B→sonar) avec usage cumulatif + debug:
  - `{ "tool": "call_llm", "params": { "message": "A→B→sonar", "model": "gpt-4o", "tool_names": ["call_llm"], "debug": true } }`
- `script_executor` basique:
  - `{ "tool": "script_executor", "params": { "script": "print('hello'); result = 2+2" } }`

---

## 9) Journalisation et erreurs
- Utiliser `logging` (pas d’`print` en prod) sauf dans sandbox `script_executor` (les prints sont capturés).
- Erreurs HTTP: lever `HTTPException` avec codes adéquats (400, 404, 500, 504, …).
- Garder les messages clairs et actionnables.

---

## 10) Processus Git & Documentation
- Commits petits, messages explicites (type: sujet — ex: `fix(script_executor): parameters schema object`).
- Éviter les refactors massifs sauf nécessité.
- Mettre à jour:
  - `LLM_DEV_GUIDE.md` lorsque vous changez les invariants/outils fondamentaux.
  - `LLM_GUIDE.md` si vous modifiez l’interface d’utilisation.
  - `src/README.md` pour les endpoints/composants serveur.
- Ouvrir une PR si changements non triviaux.

---

## 11) Variables d’environnement utiles (rappel)
- Serveur: `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`, `RELOAD`.
- LLM: `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `LLM_STREAM_TRACE`, `LLM_STREAM_DUMP`, `MCP_URL`.
- JSON/entiers: `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`.

---

Checklist avant push (LLM dev)
- [ ] Specs JSON: `parameters` est un objet; arrays ont `items`.
- [ ] Pas de régression sur `/tools` (pas d’exception à la découverte).
- [ ] `/execute` OK pour au moins un tool de test.
- [ ] Pas de blocage de boucle événementielle (opérations CPU lourdes restent côté exécuteur).
- [ ] Logs informatifs, pas verbeux par défaut.
- [ ] Docs mises à jour si changement de comportement.
