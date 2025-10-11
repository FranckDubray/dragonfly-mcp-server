




# LLM DEV GUIDE — Dragonfly MCP Server

Guide technique pour développeurs LLM. Architecture, invariants, et checklist.

---

## Architecture

**Serveur MCP (FastAPI)** exposant tools OpenAI via HTTP.

**Fichiers clés :**
- `src/app_factory.py` — FastAPI app, endpoints, CORS, auto-reload, Safe JSON
- `src/config.py` — gestion `.env`, masquage secrets
- `src/tools/` — tools (un fichier = un tool) + packages `_<tool>/` (implémentation)
- `src/tool_specs/` — specs JSON canoniques (source de vérité)

**Endpoints :**
- `GET /tools` (`?reload=1` pour rescanner)
- `POST /execute` avec `{ "tool": "<nom>", "params": {...} }`
- `GET/POST /config` (gestion .env)
- `GET /control` (panneau web)

---

## Invariants critiques

**Specs JSON :**
- `function.parameters` = **object** (jamais array)
- Arrays ont **toujours** `items`
- Utiliser `additionalProperties: false` pour cadrage strict

**Tools :**
- Python ≥ 3.11
- Fournir `run(**params) -> Any` et `spec() -> dict`
- Pas de side-effects à l'import

**Sécurité :**
- Chroot SQLite : `<projet>/sqlite3`
- Git local : limité à racine projet
- Script executor : sandbox stricte (pas d'imports)
- Pas d'accès disque hors chroot

**Performance :**
- Pas de blocage event loop
- Gros CPU → exécuteur thread via `/execute`

**⚠️ Output Size (CRITIQUE)** :
- **TOUJOURS limiter les retours massifs** (listes de 1000+ items)
- **Paramètre `limit`** avec défaut raisonnable (20-50, max 500)
- **Warning si truncated** : `{"truncated": true, "message": "..."}`
- **Retourner counts** : `total_count` vs `returned_count`
- **Exemples problématiques** : 1660 GMs, 663 streamers, 10K players → noient le LLM
- **Solution** : pagination, sampling, ou aggrégation (stats plutôt que liste complète)

---

## Créer un tool (structure correcte)

### Structure fichiers

```
src/tools/
  <tool_name>.py              # Bootstrap (SANS _) : run() + spec()
  _<tool_name>/               # Package impl (AVEC _)
    __init__.py               # Export spec()
    api.py                    # Routing
    core.py                   # Logique métier
    validators.py             # Validation pure
    utils.py                  # Helpers purs
    services/                 # I/O (HTTP, DB, files)
src/tool_specs/
  <tool_name>.json            # Spec canonique (MANDATORY)
```

### Bootstrap minimal

```python
from ._<tool_name>.api import route_operation
from ._<tool_name> import spec as _spec

def run(operation: str = None, **params):
    op = (operation or params.get("operation") or "default").strip().lower()
    if op == "some_op" and not params.get("required_param"):
        return {"error": "Parameter 'required_param' is required"}
    return route_operation(op, **params)

def spec():
    return _spec()
```

### Spec JSON

```json
{
  "type": "function",
  "function": {
    "name": "<tool_name>",
    "displayName": "<Display Name>",
    "description": "Brief description",
    "parameters": {
      "type": "object",
      "properties": {
        "operation": {"type": "string", "enum": ["op1", "op2"]},
        "array_param": {
          "type": "array",
          "items": {"type": "string"}
        },
        "limit": {
          "type": "integer",
          "description": "Max results (default: 50, max: 500)",
          "minimum": 1,
          "maximum": 500,
          "default": 50
        }
      },
      "required": ["operation"],
      "additionalProperties": false
    }
  }
}
```

---

## Checklist avant push

- [ ] `parameters` = object, arrays ont `items`
- [ ] **`limit` parameter** pour opérations retournant listes
- [ ] **Truncation warnings** si données tronquées
- [ ] **Error handling** : try-catch global dans api.py
- [ ] `GET /tools?reload=1` → tool apparaît sans erreur
- [ ] `POST /execute` → fonctionne
- [ ] Pas de blocage event loop
- [ ] Pas d'artefacts (`__pycache__/`, `*.pyc`, `sqlite3/`, `.dgy_backup/`)
- [ ] Logs clairs, pas verbeux
- [ ] Chroot respecté (fichiers, DB)

---

## Tests rapides

```bash
# Date
{"tool": "date", "params": {"operation": "today"}}

# LLM avec tools
{"tool": "call_llm", "params": {"message": "calc 23*19", "model": "gpt-4o", "tool_names": ["math"]}}

# Script executor
{"tool": "script_executor", "params": {"script": "print('hello'); result = 2+2"}}

# Chess.com avec limit
{"tool": "chess_com", "params": {"operation": "get_titled_players", "title": "GM", "limit": 10}}
```

---

## Troubleshooting

**TypeError multiple values for 'operation'** → `operation = params.pop('operation', 'default')` avant `**params`

**Reload ne prend pas un sous-module** → Restart serveur (modules déjà importés pas rechargés)

**Invalid function.parameters ([])** → `parameters` doit être objet, pas array

**call_llm n'appelle pas d'outils** → Vérifier `tool_names` avec noms exacts de `/tools`

**Timeout 300s bloqué** → Vérifier timeout dans spec JSON + validator Python

**Erreur 500 non catchée** → Ajouter try-catch global dans api.py retournant `{"error": "..."}`

**Output trop massif (1000+ items)** → Ajouter `limit` param (défaut 50, max 500) + truncation warning

---

## call_llm (orchestrateur 2 phases)

**Phase 1** (avec tools) : collecte `tool_calls` + exécution serveur  
**Phase 2** (sans tools) : génération texte final

**Paramètres clés :** `message` (requis), `model` (requis), `tool_names` (array de noms techniques), `promptSystem`, `max_tokens`, `debug`

**Usage :** `tool_names` = noms exacts retournés par `/tools` (ex: `["math", "date"]`)

---

## script_executor (sandbox)

**Paramètres :** `script` (requis), `variables` (dict), `timeout` (def 60, max 300), `allowed_tools` (whitelist)

**API limitée :** print, json, time.lite, math  
**Pas d'imports**, builtins restreints  
**Appels tools :** `call_tool("<nom>", **params)` ou `tools.<nom>(**params)`

---

## Variables d'env utiles

**Serveur :** `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`  
**LLM :** `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `MCP_URL`  
**JSON :** `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`  
**Academic :** `ACADEMIC_RS_MAX_ITEMS`, `ACADEMIC_RS_MAX_ABSTRACT_CHARS`, `ACADEMIC_RS_MAX_BYTES`

---

## Safe JSON

`sanitize_for_json()` + `SafeJSONResponse` (dans `app_factory.py`) :
- Convertit très grands entiers en strings si `BIGINT_AS_STRING=1`
- `NaN`/`Infinity`/`-Infinity` → strings
- Ne pas contourner cette hygiène

---

## Output Size Best Practices

### ⚠️ Problème : Noyer le LLM

- **1660 GMs** → contexte explosé, réponse inutilisable
- **663 streamers** → parsing impossible pour le LLM
- **10K+ players d'un pays** → timeout, mémoire, coût tokens

### ✅ Solution : Limiter intelligemment

**1. Paramètre `limit` obligatoire**
```json
{
  "limit": {
    "type": "integer",
    "description": "Max results (default: 50, max: 500)",
    "minimum": 1,
    "maximum": 500,
    "default": 50
  }
}
```

**2. Validation dans validators.py**
```python
def validate_limit(limit: Any, default: int = 50) -> int:
    if limit is None:
        return default
    if not isinstance(limit, int):
        return default
    return max(1, min(limit, 500))
```

**3. Truncation dans core.py**
```python
def get_massive_list(limit: int = 50):
    all_items = fetch_all()  # 1000+ items
    total = len(all_items)
    truncated = total > limit
    items = all_items[:limit]
    
    result = {
        'total_count': total,
        'returned_count': len(items),
        'items': items,
    }
    
    if truncated:
        result['truncated'] = True
        result['message'] = f"Showing {limit} of {total}. Increase 'limit' to see more (max 500)."
    
    return result
```

**4. Alternatives aux listes massives**

- **Agrégation** : retourner stats plutôt que liste complète
- **Sampling** : random sample de N items représentatifs
- **Pagination** : offset/limit pour parcourir par chunks
- **Filtres** : permettre au LLM de filtrer avant fetch

**Exemple :**
```python
# ❌ BAD: 1660 GMs complets
return {'gms': all_1660_gms}

# ✅ GOOD: Top 50 + stats
return {
    'total_gms': 1660,
    'top_50': top_50_gms,
    'countries_represented': 87,
    'average_rating': 2650,
}
```

---

## Ressources

**Tools simples :** `date.py`, `sqlite_db.py`  
**Tools modulaires :** `imap.py` + `_imap/`, `git.py` + `_git/`, `chess_com.py` + `_chess_com/`

**Pour comprendre :** regarder `chess_com.py` (bootstrap) puis `_chess_com/` (architecture avec limit)

---

**Commits petits et explicites. Mettre à jour ce guide si changement d'invariants.**

 
 
 
 
