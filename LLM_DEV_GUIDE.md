# LLM DEV GUIDE — Dragonfly MCP Server (MàJ 2025‑10)

Guide à l'attention d'un LLM « développeur » qui modifie/étend ce dépôt. Vous y trouverez l'architecture, les invariants à respecter, les limites, ainsi que les correctifs récents à connaître pour éviter les régressions.

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
- `src/server.py` — point d'entrée Uvicorn (ne pas y mettre de logique métier).
- `src/app_factory.py` — création de l'app FastAPI, endpoints, CORS, découverte/auto‑reload, Safe JSON.
- `src/config.py` — gestion du `.env`, masquage des secrets, racine projet.
- `src/tools/` — tools (un fichier par outil) + sous‑packages spécialisés:
  - `_call_llm/` — orchestrateur LLM (streaming), HTTP client, parsing SSE, exécution des tool_calls, debug utils.
  - `_math/` — calcul num/HP/symbolique.
  - `_script/` — exécution sandbox (ScriptExecutor) utilisée par `script_executor`.
  - `_git/`, `_gitbook/`, `_reddit/`, `_universal_doc/`, `_imap/`, `_pdf_download/` …
- `src/tool_specs/` — specs JSON canoniques (certaines sources de vérité côté client LLM).
- `src/README.md` — doc API côté serveur (endpoints + composants).

---

## 3) Invariants et conventions (critiques)
- Python ≥ 3.11 ; privilégier les annotations de type.
- Un tool doit fournir:
  - `run(**params) -> Any`
  - `spec() -> dict` de type OpenAI `function`.
- Spécifications JSON:
  - `function.parameters` est un objet (ou booléen), jamais un tableau.
  - Toute `array` a un `items`.
  - Utiliser `additionalProperties: false` quand utile pour cadrer les appels.
- Découverte des tools: évitez les side‑effects non idempotents à l'import.
- Sécurité: ne pas affaiblir la sandbox de `script_executor`; pas d'accès disque hors chroot; respecter la chroot SQLite (DB sous `<projet>/sqlite3`).
- Perf: ne bloquez pas l'event loop; gros CPU → exécuteur (thread) via `/execute`.

---

## 4) Orchestrateur `call_llm` (2 phases)
- 1er stream (avec tools): collecte des `tool_calls`, exécution côté serveur.
- 2e stream (sans tools): génération finale (texte).
- Paramètres clés: `message` (requis), `model` (requis), `tool_names` (liste d'outils exposés), `promptSystem`, `max_tokens`, `debug`.
- Debug: les résumés de payload n'affichent plus `tool_choice`/`parallel_tool_calls` (évite champs nulls). 
- Bon usage de `tool_names`: utilisez les noms techniques de `/tools` (champ `name`), ex: `["math","date"]`.

---

## 5) `script_executor` (sandbox multi‑tools)
- Paramètres: `script` (obligatoire), `variables` (dict), `timeout` (def 60), `allowed_tools` (whitelist optionnelle).
- Compatibilité: si l'ancienne classe `ScriptExecutor` ne supporte pas `allowed_tools`, le wrapper retombe sans whitelist et renvoie un warning.
- Échecs fréquents et aide:
  - Tool inconnu → vérifier `available_tools` renvoyés.
  - Tool non autorisé → revoir `allowed_tools`.
  - Limite d'appels d'outils → réduire les appels.
  - Timeout → simplifier le script.
- Sécurité: pas d'imports, builtins limités, API restreinte (print, json, time.lite, etc.).

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
  - `max_bytes` (def 200000 ≈ 200KB) — tronque/ébranche jusqu'à respecter la limite et ajoute une note explicative.

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
- pdf_download
  - `{ "tool": "pdf_download", "params": { "operation": "download", "url": "https://arxiv.org/pdf/2301.00001.pdf", "filename": "paper" } }`

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
  - `docs/` (PDFs téléchargés, etc.)
- Ne pas forcer leur ajout (éviter `git add -f`).
- Option: ajouter un hook `pre-commit` pour bloquer ces patterns.

---

## 13) Variables d'environnement utiles
- Serveur: `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`, `RELOAD`.
- LLM: `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `LLM_STREAM_TRACE`, `LLM_STREAM_DUMP`, `MCP_URL`.
- JSON/entiers: `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`.
- Recherche: `ACADEMIC_RS_MAX_ITEMS`, `ACADEMIC_RS_MAX_ABSTRACT_CHARS`, `ACADEMIC_RS_MAX_BYTES`.

---

## 14) Checklist avant push
- [ ] Specs JSON: `parameters` est un objet; arrays ont `items`; pas de champs superflus.
- [ ] `GET /tools?reload=1` fonctionne, pas d'exception à la découverte.
- [ ] `POST /execute` OK sur un outil de test (ex: `date`, `script_executor`).
- [ ] Pas de blocage d'event loop (travaux CPU lourds → exécuteur).
- [ ] Logs informatifs, pas verbeux par défaut.
- [ ] Hygiène: pas d'artefacts (`__pycache__/`, `*.pyc`, `sqlite3/`, `.dgy_backup/`, `egg-info`).
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
- `call_llm` n'appelle pas d'outils ?
  - Vérifier `tool_names` et les noms exacts renvoyés par `/tools`.

---

Contribuez avec de petits commits explicites. Mettez à jour ce guide si vous changez les invariants/outils fondamentaux.


## 16) Guide express: créer un tool MCP du premier coup

Objectif: livrer un outil qui s'enregistre sans erreur, passe les validations, et fonctionne immédiatement via POST /execute.

### A. Structure des fichiers (CRITIQUE - éviter l'erreur #1)

**❌ ERREUR COMMUNE :**
```
src/tools/
  pdf_download/          ← FAUX ! Pas de underscore
    __init__.py
    api.py
    core.py
```

**✅ STRUCTURE CORRECTE :**
```
src/tools/
  pdf_download.py        ← Bootstrap file (SANS underscore)
  _pdf_download/         ← Package implémentation (AVEC underscore)
    __init__.py
    api.py
    core.py
    validators.py
    utils.py
    services/
      downloader.py
```

**🔑 RÈGLE D'OR :**
- **Fichier bootstrap** : `src/tools/<tool_name>.py` (SANS `_`)
  - C'est ce fichier que le serveur découvre
  - Contient `run()` et `spec()` qui délèguent au package
- **Package d'implémentation** : `src/tools/_<tool_name>/` (AVEC `_`)
  - Le underscore le rend invisible au scanner de tools
  - Contient toute la logique métier

### B. Fichier bootstrap minimal (src/tools/<tool_name>.py)

```python
"""<Tool Name> - brief description.

Example:
    {
        "tool": "<tool_name>",
        "params": {
            "operation": "...",
            ...
        }
    }
"""
from __future__ import annotations
from typing import Dict, Any

# Import depuis le package d'implémentation (avec _)
from ._<tool_name>.api import route_operation
from ._<tool_name> import spec as _spec


def run(operation: str = None, **params) -> Dict[str, Any]:
    """Execute <tool_name> operation.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "default_op").strip().lower()
    
    # Validate required params
    if op == "some_op":
        if not params.get("required_param"):
            return {"error": "Parameter 'required_param' is required"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
```

### C. Package d'implémentation (__init__.py)

```python
"""<Tool Name> package - internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    # Load from canonical JSON file
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "<tool_name>.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "<tool_name>",
                "displayName": "<Tool Display Name>",
                "description": "Brief description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["op1"]},
                        # ... other params
                    },
                    "required": ["operation"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
```

### D. Spécification JSON (src/tool_specs/<tool_name>.json)

```json
{
  "type": "function",
  "function": {
    "name": "<tool_name>",
    "displayName": "<Tool Display Name>",
    "description": "Brief description of what this tool does",
    "parameters": {
      "type": "object",
      "properties": {
        "operation": {
          "type": "string",
          "enum": ["op1", "op2"],
          "description": "Operation to perform"
        },
        "param1": {
          "type": "string",
          "description": "Description of param1"
        },
        "array_param": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Array parameter (items MANDATORY)"
        }
      },
      "required": ["operation"],
      "additionalProperties": false
    }
  }
}
```

### E. Architecture modulaire recommandée

```
src/tools/_<tool_name>/
├── __init__.py              # Exports spec()
├── api.py                   # Routing (route_operation)
├── core.py                  # Business logic (handle_xxx functions)
├── validators.py            # Input validation/normalization
├── utils.py                 # Pure helpers (no I/O)
├── services/                # External I/O (isolated)
│   ├── __init__.py
│   └── service_name.py      # HTTP, DB, file operations
└── README.md                # Tool-specific documentation
```

**Séparation des responsabilités :**
- `api.py` : parsing + routing → appelle `core.py`
- `core.py` : logique métier → appelle `validators.py`, `utils.py`, `services/`
- `validators.py` : validation pure (pas d'I/O)
- `utils.py` : helpers purs (pas d'I/O)
- `services/` : toutes les I/O externes (HTTP, DB, fichiers)

### F. Exemple complet : pdf_download

**1. Bootstrap file** (`src/tools/pdf_download.py`)
```python
from ._pdf_download.api import route_operation
from ._pdf_download import spec as _spec

def run(operation: str = "download", **params):
    op = (operation or params.get("operation") or "download").strip().lower()
    if op == "download" and not params.get("url"):
        return {"error": "Parameter 'url' is required"}
    return route_operation(op, **params)

def spec():
    return _spec()
```

**2. API layer** (`src/tools/_pdf_download/api.py`)
```python
from .core import handle_download

def route_operation(operation: str, **params):
    if operation == "download":
        return handle_download(
            url=params.get("url"),
            filename=params.get("filename"),
            overwrite=params.get("overwrite", False),
            timeout=params.get("timeout", 60)
        )
    return {"error": f"Unknown operation: {operation}"}
```

**3. Core logic** (`src/tools/_pdf_download/core.py`)
```python
from .validators import validate_url, validate_filename
from .utils import get_unique_filename, ensure_docs_pdfs_directory
from .services.downloader import download_pdf, save_pdf_to_file

def handle_download(url, filename=None, overwrite=False, timeout=60):
    # Validate
    url_result = validate_url(url)
    if not url_result["valid"]:
        return {"error": url_result["error"]}
    
    # Process
    docs_pdfs = ensure_docs_pdfs_directory()
    final_filename = get_unique_filename(docs_pdfs, filename, overwrite)
    
    # Download
    download_result = download_pdf(url, timeout)
    if not download_result["success"]:
        return {"error": download_result["error"]}
    
    # Save
    save_result = save_pdf_to_file(download_result["content"], docs_pdfs / final_filename)
    
    return {"success": True, "file": {"filename": final_filename}}
```

### G. Sécurité et hygiène (crucial)

**Validation des entrées :**
```python
def validate_url(url: str) -> Dict[str, Any]:
    if not url or not isinstance(url, str):
        return {"valid": False, "error": "URL must be a non-empty string"}
    
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return {"valid": False, "error": "URL must use http or https"}
    
    return {"valid": True, "url": url}
```

**Chroot pour fichiers :**
```python
def ensure_docs_pdfs_directory() -> Path:
    """Ensure docs/pdfs exists within project root."""
    project_root = Path(__file__).parent.parent.parent.parent
    docs_pdfs = project_root / "docs" / "pdfs"
    docs_pdfs.mkdir(parents=True, exist_ok=True)
    return docs_pdfs
```

**Validation de contenu (exemple PDF) :**
```python
def is_pdf_content(content: bytes) -> bool:
    """Check PDF magic bytes: %PDF-"""
    if not content or len(content) < 5:
        return False
    return content[:5] == b'%PDF-'
```

### H. Test rapide (manuel)

```bash
# 1. Reload tools
curl "http://127.0.0.1:8000/tools?reload=1" | jq '.tools[] | select(.id == "<tool_name>")'

# 2. Execute
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"tool":"<tool_name>","params":{"operation":"op1",...}}' | jq
```

### I. Pièges fréquents et corrections

**❌ Erreur #1 : Mauvaise structure de dossier**
```
pdf_download/           ← FAUX
  __init__.py
```
**✅ Correction :**
```
pdf_download.py         ← Bootstrap
_pdf_download/          ← Implémentation
  __init__.py
```

**❌ Erreur #2 : Spec sans items pour array**
```json
"files": {
  "type": "array"       ← FAUX : manque items
}
```
**✅ Correction :**
```json
"files": {
  "type": "array",
  "items": {"type": "string"}
}
```

**❌ Erreur #3 : Parameters = tableau**
```json
"parameters": []        ← FAUX
```
**✅ Correction :**
```json
"parameters": {
  "type": "object",
  "properties": {...}
}
```

**❌ Erreur #4 : Logique dans __init__.py du package**
```python
# src/tools/_pdf_download/__init__.py
def run(...):           ← FAUX : la logique doit être ailleurs
    # business logic here
```
**✅ Correction :**
```python
# src/tools/pdf_download.py (bootstrap)
def run(...):
    return route_operation(...)

# src/tools/_pdf_download/core.py
def handle_operation(...):
    # business logic here
```

### J. Check‑list "first‑time‑right"

**Structure :**
- [ ] Bootstrap file : `src/tools/<tool_name>.py` (SANS `_`)
- [ ] Package impl : `src/tools/_<tool_name>/` (AVEC `_`)
- [ ] Spec JSON : `src/tool_specs/<tool_name>.json`

**Code :**
- [ ] `run()` et `spec()` dans bootstrap file
- [ ] `spec()` dans `_<tool_name>/__init__.py`
- [ ] Routing dans `api.py`
- [ ] Logique métier dans `core.py`

**Spec JSON :**
- [ ] `parameters` = object (pas array)
- [ ] Arrays ont `items`
- [ ] `additionalProperties: false`
- [ ] `required` liste les champs obligatoires

**Sécurité :**
- [ ] Validation des entrées (types, ranges)
- [ ] Chroot pour fichiers (pas d'accès hors projet)
- [ ] Validation de contenu (magic bytes si applicable)
- [ ] Pas de secrets dans logs

**Tests :**
- [ ] `GET /tools?reload=1` → tool apparaît
- [ ] Spec JSON valide (pas d'erreurs)
- [ ] `POST /execute` → résultat attendu
- [ ] Erreurs retournent `{"error": "message"}` explicite

### K. Exemple réel : erreur évitée grâce au guide

**Situation initiale (FAUX) :**
```
src/tools/
  pdf_download/                    ← Erreur : pas de _
    __init__.py                    ← Contient run() et spec()
    api.py
    core.py
```

**Problème :** Le scanner découvre `pdf_download/` comme module, mais ne trouve pas `run()` et `spec()` directement importables.

**Correction appliquée (CORRECT) :**
```
src/tools/
  pdf_download.py                  ← Bootstrap découvert par scanner
  _pdf_download/                   ← Package ignoré par scanner
    __init__.py                    ← Exporte spec()
    api.py
    core.py
```

**Résultat :** Tool découvert et fonctionnel immédiatement ! ✅

---

## 17) Ressources et exemples

**Tools simples (1 fichier) :**
- `src/tools/date.py` - opérations date/heure
- `src/tools/sqlite_db.py` - SQLite avec chroot

**Tools modulaires (package) :**
- `src/tools/imap.py` + `src/tools/_imap/` - IMAP multi-comptes
- `src/tools/git.py` + `src/tools/_git/` - Git unifié
- `src/tools/pdf_download.py` + `src/tools/_pdf_download/` - PDF download

**Pour comprendre :**
1. Regarder d'abord `pdf_download.py` (bootstrap simple)
2. Puis explorer `_pdf_download/` (architecture modulaire)
3. Comparer avec `imap.py` / `_imap/` (pattern similaire)

---

**En cas de doute, demandez ou consultez les exemples existants !**
