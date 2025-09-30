# LLM DEV GUIDE — Dragonfly MCP Server (MàJ 2025‑09)

Guide à l’attention d’un LLM « développeur » qui modifie/étend ce dépôt. Vous y trouverez l’architecture, les invariants à respecter, les limites, ainsi que les correctifs récents à connaître pour éviter les régressions.

---

## 0) Changements récents (à ne pas casser)
- Specs JSON
  - Les `function.parameters` DOIVENT être un objet (ou booléen), jamais un tableau. Cas corrigé: `script_executor.json` (remplacé un `[]` invalide).
  - Toute propriété de type `array` doit définir `items` (ex: `tool_names` de `call_llm`).
  - Garder `additionalProperties: false` quand pertinent.
- call_llm (orchestration 2 phases)
  - Paramètre pour exposer des outils: `tool_names` (array de strings = noms techniques retournés par `/tools`).
  - En mode debug, on n’expose plus `tool_choice` ni `parallel_tool_calls` dans les payload summaries.
- script_executor (sandbox)
  - Supporte une whitelist `allowed_tools` (liste de noms d’outils). Un fallback de compatibilité existe si l’ancienne signature est rencontrée.
  - Rappels sécurité: pas d’imports, API limitée, appels aux outils via `call_tool(...)` ou `tools.<nom>(...)`.
- academic_research_super (Recherche multi‑sources)
  - Sources intégrées: arXiv, PubMed (ESearch+ESummary), CrossRef, HAL.
  - Filtre client du segment `submittedDate:[NOW‑XDAYS TO NOW]` + post‑filtrage locale des dates.
  - Déduplication/fusion cross‑sources par DOI→URL→titre+date, tri global par date desc.
  - Garde‑fous de taille: `include_abstracts`, `max_total_items` (def 50), `max_abstract_chars` (def 2000), `max_bytes` (def ≈200KB).
- Hygiène Git (public)
  - Ignorés: `.dgy_backup/`, `sqlite3/` (bases locales), `__pycache__/`, `**/__pycache__/`, `*.pyc`, `src/add_mcp_server.egg-info/`.
  - Les artefacts déjà poussés ont été supprimés de `main`.

---

## 1) Objectif et architecture
- Serveur MCP (FastAPI) exposant des « tools » (OpenAI tools) en HTTP.
- Découverte dynamique des tools dans `src/tools/` (chaque outil = module Python avec `run()` et `spec()`).
- Endpoints principaux:
  - `GET /tools` (ajouter `?reload=1` pour rescanner)
  - `POST /execute` avec `{ tool: string, params: object }`
  - `GET/POST /config` (gestion .env)
  - `GET /control` / `GET /control.js`
- JSON « sûr »: très grands entiers, NaN/Inf, etc. sont assainis (cf. `sanitize_for_json()` et `SafeJSONResponse`).

---

## 2) Carte rapide du code
- `src/server.py` — point d’entrée Uvicorn (ne pas y mettre de logique métier).
- `src/app_factory.py` — création de l’app FastAPI, endpoints, CORS, découverte/auto‑reload, Safe JSON.
- `src/config.py` — gestion du `.env`, masquage des secrets, racine projet.
- `src/tools/` — tools (un fichier par outil) + sous‑packages spécialisés:
  - `_call_llm/` — orchestrateur LLM (streaming), HTTP client, parsing SSE, exécution des tool_calls, debug utils.
  - `_math/` — calcul num/HP/symbolique.
  - `_script/` — exécution sandbox (ScriptExecutor) utilisée par `script_executor`.
  - `_git/`, `_gitbook/`, `_reddit/`, `_universal_doc/` …
- `src/tool_specs/` — specs JSON canoniques (certaines sources de vérité côté client LLM).
- `src/README.md` — doc API côté serveur (endpoints + composants).

---

## 3) Invariants et conventions (critiques)
- Python ≥ 3.9 ; privilégier les annotations de type.
- Un tool doit fournir:
  - `run(**params) -> Any`
  - `spec() -> dict` de type OpenAI `function`.
- Spécifications JSON:
  - `function.parameters` est un objet (ou booléen), jamais un tableau.
  - Toute `array` a un `items`.
  - Utiliser `additionalProperties: false` quand utile pour cadrer les appels.
- Découverte des tools: évitez les side‑effects non idempotents à l’import.
- Sécurité: ne pas affaiblir la sandbox de `script_executor`; pas d’accès disque hors chroot; respecter la chroot SQLite (DB sous `<projet>/sqlite3`).
- Perf: ne bloquez pas l’event loop; gros CPU → exécuteur (thread) via `/execute`.

---

## 4) Orchestrateur `call_llm` (2 phases)
- 1er stream (avec tools): collecte des `tool_calls`, exécution côté serveur.
- 2e stream (sans tools): génération finale (texte).
- Paramètres clés: `message` (requis), `model` (requis), `tool_names` (liste d’outils exposés), `promptSystem`, `max_tokens`, `debug`.
- Debug: les résumés de payload n’affichent plus `tool_choice`/`parallel_tool_calls` (évite champs nulls). 
- Bon usage de `tool_names`: utilisez les noms techniques de `/tools` (champ `name`), ex: `["math","date"]`.

---

## 5) `script_executor` (sandbox multi‑tools)
- Paramètres: `script` (obligatoire), `variables` (dict), `timeout` (def 60), `allowed_tools` (whitelist optionnelle).
- Compatibilité: si l’ancienne classe `ScriptExecutor` ne supporte pas `allowed_tools`, le wrapper retombe sans whitelist et renvoie un warning.
- Échecs fréquents et aide:
  - Tool inconnu → vérifier `available_tools` renvoyés.
  - Tool non autorisé → revoir `allowed_tools`.
  - Limite d’appels d’outils → réduire les appels.
  - Timeout → simplifier le script.
- Sécurité: pas d’imports, builtins limités, API restreinte (print, json, time.lite, etc.).

---

## 6) `academic_research_super` (recherche multi‑sources)
- Sources: arXiv, PubMed (ESearch+ESummary), CrossRef, HAL.
- Filtrage client `submittedDate:[NOW‑XDAYS TO NOW]`: retiré de la query envoyée, post‑filtrage local par date.
- Filtres année `year_from`/`year_to` (parsing souple des dates fournisseurs).
- Fusion/déduplication cross‑sources: clé DOI → URL → titre+date; préservation des champs non vides; auteurs = plus longue liste; abstract = plus long (si `include_abstracts`), `citations_count` = max.
- Tri global par date desc.
- Garde‑fous de taille (prévention noyade LLM):
  - `include_abstracts` (bool; si false, abstracts vides)
  - `max_total_items` (def 50)
  - `max_abstract_chars` (def 2000; 0 si `include_abstracts=false`)
  - `max_bytes` (def 200000 ≈ 200KB) — tronque/ébranche jusqu’à respecter la limite et ajoute une note explicative.

---

## 7) Safe JSON & grands entiers
- `sanitize_for_json()` + `SafeJSONResponse` (dans `app_factory.py`):
  - Convertit en chaîne les entiers énormes (> `BIGINT_STR_THRESHOLD`) si `BIGINT_AS_STRING=1`.
  - Rend `NaN`/`Infinity`/`-Infinity` en chaînes.
  - Lève la limite `int->str` Python si `PY_INT_MAX_STR_DIGITS` est défini.
- Ne pas contourner cette hygiène via des sérialisations custom.

---

## 8) Flux de dev
- Démarrer: `./scripts/dev.sh` (ou `scripts/dev.ps1` sous Windows).
- Rafraîchir la liste des tools: `GET /tools?reload=1`.
- Exécuter un tool: `POST /execute` → `{ "tool": "<nom>", "params": { ... } }`.
- Config: `GET/POST /config`.
- Note: la découverte reload les modules `tools.<nom>` mais pas toujours les sous‑modules déjà importés (ex: `tools._script.*`). En cas de doute, redémarrez le serveur.

---

## 9) Ajouter/Modifier un tool
- Créez `src/tools/<tool>.py` avec `run()` et `spec()`.
- Option: `src/tool_specs/<tool>.json` si vous voulez une spec canonique (et plus stricte côté LLM).
- Vérifiez:
  - `GET /tools?reload=1` → le tool apparaît, la spec est valide (parameters=object; arrays→items).
  - `POST /execute` avec un cas basique.

---

## 10) Tests manuels rapides
- Date
  - `{ "tool": "date", "params": { "operation": "today" } }`
- call_llm simple
  - `{ "tool": "call_llm", "params": { "message": "Bonjour", "model": "gpt-4o" } }`
- call_llm avec tools
  - `{ "tool": "call_llm", "params": { "message": "calc 23*19", "model": "gpt-4o", "tool_names": ["math"] } }`
- script_executor
  - `{ "tool": "script_executor", "params": { "script": "print('hello'); result = 2+2" } }`
- academic_research_super (fenêtre 7 jours)
  - `{ "tool": "academic_research_super", "params": { "operation": "search_papers", "query": "LLM AND submittedDate:[NOW-7DAYS TO NOW]", "sources": ["arxiv"], "max_results": 5 } }`

---

## 11) Journalisation & erreurs
- Utiliser `logging` (sauf sandbox où `print` est capturé).
- Coder des erreurs HTTP claires (`HTTPException` 400/404/500/504…).
- Messages actionnables.

---

## 12) Hygiène Git & répertoires ignorés
- `.gitignore` inclut:
  - `.dgy_backup/` (backups internes)
  - `sqlite3/` (DB locales)
  - `__pycache__/`, `**/__pycache__/`, `*.pyc` (artefacts Python)
  - `src/add_mcp_server.egg-info/` (métadonnées build)
- Ne pas forcer leur ajout (éviter `git add -f`).
- Option: ajouter un hook `pre-commit` pour bloquer ces patterns.

---

## 13) Variables d’environnement utiles
- Serveur: `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`, `RELOAD`.
- LLM: `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `LLM_STREAM_TRACE`, `LLM_STREAM_DUMP`, `MCP_URL`.
- JSON/entiers: `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`.
- Recherche: `ACADEMIC_RS_MAX_ITEMS`, `ACADEMIC_RS_MAX_ABSTRACT_CHARS`, `ACADEMIC_RS_MAX_BYTES`.

---

## 14) Checklist avant push
- [ ] Specs JSON: `parameters` est un objet; arrays ont `items`; pas de champs superflus.
- [ ] `GET /tools?reload=1` fonctionne, pas d’exception à la découverte.
- [ ] `POST /execute` OK sur un outil de test (ex: `date`, `script_executor`).
- [ ] Pas de blocage d’event loop (travaux CPU lourds → exécuteur).
- [ ] Logs informatifs, pas verbeux par défaut.
- [ ] Hygiène: pas d’artefacts (`__pycache__/`, `*.pyc`, `sqlite3/`, `.dgy_backup/`, `egg-info`).
- [ ] Si vous touchez `call_llm`, ne réintroduisez pas `tool_choice`/`parallel_tool_calls` dans le debug.
- [ ] Si vous touchez `script_executor`, gardez la compatibilité `allowed_tools` (fallback propre).
- [ ] Si vous touchez `academic_research_super`, respectez les limites de taille et la déduplication.

---

## 15) Dépannage
- Un `TypeError got multiple values for keyword argument 'operation'` ?
  - Capturez `operation = params.pop('operation', 'search_papers')` avant `**params`.
- Le reload ne prend pas une modif sous‑module (ex: `_script/executor.py`) ?
  - Redémarrer le serveur (les sous‑modules déjà importés ne sont pas toujours rechargés par la discovery).
- Erreur `Invalid function.parameters ([])` ?
  - Corriger la spec: `parameters` doit être un objet; jamais un tableau.
- `call_llm` n’appelle pas d’outils ?
  - Vérifier `tool_names` et les noms exacts renvoyés par `/tools`.

---

Contribuez avec de petits commits explicites. Mettez à jour ce guide si vous changez les invariants/outils fondamentaux.
