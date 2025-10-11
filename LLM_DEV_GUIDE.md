
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
- **`category` obligatoire** : choisir parmi les 10 catégories canoniques ci‑dessous (clé exacte)
- Optionnel: `tags` (ex: `external_sources`, `knowledge`, `social`, `scraping`, `docs`, `search`) pour un filtre UI fin (ne pas créer de nouvelles catégories)

**Tools :**
- Python ≥ 3.11
- Fournir `run(**params) -> Any` et `spec() -> dict`
- `spec()` doit charger le JSON canonique (src/tool_specs/<tool_name>.json). Ne pas dupliquer le schéma en Python.
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
- TOUJOURS limiter les retours massifs (listes de 1000+ items)
- Paramètre `limit` avec défaut raisonnable (20-50, max 500)
- Warning si truncated : `{"truncated": true, "message": "..."}`
- Retourner counts : `total_count` vs `returned_count`

---

## Catégories canoniques (10 clés OBLIGATOIRES)

La valeur `function.category` de chaque tool DOIT être exactement l'une de ces clés:

| Catégorie (UI) | Clé (JSON) | Emoji | Exemples |
|----------------|------------|-------|----------|
| Intelligence & Orchestration | `intelligence` | 📊 | call_llm, ollama_local, academic_research_super |
| Development | `development` | 🔧 | git, gitbook, script_executor |
| Communication | `communication` | 📧 | imap, email_send, discord_webhook |
| Data & Storage | `data` | 🗄️ | sqlite_db, excel_to_sqlite |
| Documents | `documents` | 📄 | pdf_download, pdf_search, pdf2text, office_to_pdf, universal_doc_scraper |
| Media | `media` | 🎬 | youtube_search, youtube_download, video_transcribe, ffmpeg_frames, generate_edit_image |
| Transportation | `transportation` | ✈️ | flight_tracker, ship_tracker, aviation_weather, velib |
| Networking | `networking` | 🌐 | http_client |
| Utilities | `utilities` | 🔢 | math, date |
| Social & Entertainment | `entertainment` | 🎮 | chess_com, reddit_intelligence |

Notes:
- Le champ `category` n'est pas exposé dans l'API `/tools` (uniquement utilisé par l'UI pour grouper). L’UI affiche "Social & Entertainment" pour la clé `entertainment`.
- Ne créez pas de nouvelles clés de catégorie. Utilisez des `tags` pour marquer les outils "bases de connaissance externes" (ex: `external_sources`).

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
import json, os

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', '<tool_name>.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### Spec JSON (exemple)

```json
{
  "type": "function",
  "function": {
    "name": "<tool_name>",
    "displayName": "<Display Name>",
    "category": "intelligence",
    "tags": ["external_sources"],
    "description": "Brief description",
    "parameters": {
      "type": "object",
      "properties": {
        "operation": {"type": "string", "enum": ["op1", "op2"]},
        "array_param": {"type": "array", "items": {"type": "string"}},
        "limit": {"type": "integer", "description": "Max results (default: 50, max: 500)", "minimum": 1, "maximum": 500, "default": 50}
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
- [ ] `category` définie (une des 10 clés valides)
- [ ] `tags` si utile (ex: `external_sources`, `knowledge`)
- [ ] `limit` parameter pour opérations retournant listes
- [ ] Truncation warnings si données tronquées
- [ ] Error handling : try-catch global dans api.py
- [ ] `GET /tools?reload=1` → tool apparaît sans erreur
- [ ] `POST /execute` → fonctionne
- [ ] Pas de blocage event loop
- [ ] Pas d'artefacts (`__pycache__/`, `*.pyc`, `sqlite3/`, `.dgy_backup/`)
- [ ] Logs clairs, pas verbeux
- [ ] Chroot respecté (fichiers, DB)
