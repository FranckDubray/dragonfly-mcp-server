# LLM DEV GUIDE — Dragonfly MCP Server

Guide technique pour développeurs LLM. Architecture, invariants, checklist, et politique d'archivage du changelog.

---

## Architecture

**Serveur MCP (FastAPI)** exposant tools OpenAI via HTTP.

**Fichiers clés :**
- `src/app_factory.py` — FastAPI app, endpoints, CORS, auto-reload, Safe JSON
- `src/config.py` — gestion `.env`, masquage secrets
- `src/tools/` — tools (un fichier = un tool) + packages `_<tool>/` (implémentation)
- `src/tool_specs/` — specs JSON canoniques (source de vérité)
- `scripts/generate_tools_catalog.py` — génère automatiquement `src/tools/README.md` à partir des specs

**Endpoints :**
- `GET /tools` (`?reload=1` pour rescanner)
- `POST /execute` avec `{ "tool": "<nom>", "params": {...} }`
- `GET/POST /config` (gestion .env)
- `GET /control` (panneau web)

---

## Catalogue des tools (auto‑généré)

- Le fichier `src/tools/README.md` est désormais AUTO‑GÉNÉRÉ par `scripts/generate_tools_catalog.py` à partir des specs canoniques dans `src/tool_specs/*.json`.
- Ne PAS éditer `src/tools/README.md` à la main. Les modifications doivent se faire dans les specs JSON et (optionnellement) dans le fichier meta.
- Optionnel: métadonnées complémentaires dans `src/tool_specs/_meta/tools_meta.json` (ex: `tokens` requis, notes, pricing). Si absent, la génération continue sans.
- Les scripts de dev exécutent automatiquement la génération au démarrage:
  - Unix: `./scripts/dev.sh` → exécute `python3 scripts/generate_tools_catalog.py`
  - Windows: `./scripts/dev.ps1` → exécute `python scripts/generate_tools_catalog.py`

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
- `spec()` doit charger le JSON canonique (`src/tool_specs/<tool_name>.json`). Ne pas dupliquer le schéma en Python.
- Pas de side-effects à l'import

**Sécurité :**
- Chroot SQLite : `<projet>/sqlite3`
- Git local : limité à racine projet
- Script executor : sandbox stricte (pas d'import dynamiques)
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
- Le champ `category` n'est pas exposé dans l'API `/tools` (uniquement utilisé par l'UI pour grouper). L'UI affiche "Social & Entertainment" pour la clé `entertainment`.
- Ne créez pas de nouvelles clés de catégorie. Utilisez des `tags` pour marquer les outils "bases de connaissance externes" (ex: `external_sources`).

---

## Politique d'archivage du CHANGELOG (rotation)

Objectif: garder un CHANGELOG lisible à la racine tout en préservant l'historique complet.

Règles:
- Racine: `CHANGELOG.md` ne contient que les ≤ 10 dernières releases (les plus récentes).
- Archives: créer un répertoire `changelogs/`.
- Format d'archive: 1 fichier par tranche de 10 releases, en partant de la première.
  - Exemples:
    - `changelogs/CHANGELOG_1.0.0_to_1.9.x.md`
    - `changelogs/CHANGELOG_1.10.0_to_1.19.x.md`
- Contenu: l'archive doit contenir le TEXTE INTÉGRAL d'époque (pas de simplification, pas de résumés).
- Le `CHANGELOG.md` racine inclut en tête la note: "Older entries have been archived under changelogs/ (range-based files)."

Procédure (manuelle ou scriptée):
1) Quand une nouvelle release dépasse la fenêtre de 10 versions récentes:
   - Déplacer les plus anciennes entrées hors fenêtre vers le fichier d'archive de la tranche correspondante (créer le fichier si absent).
   - Conserver à la racine uniquement les 10 plus récentes.
2) Ne pas modifier le wording historique lors du déplacement.
3) Commit standard: `docs(changelog): rotate changelog, archive versions X → Y`

Option script (recommandé):
- `scripts/archive_changelog.py` qui:
  - Parse `CHANGELOG.md`
  - Identifie les sections par version
  - Déplace les versions hors fenêtre dans la bonne tranche d'archive
  - Maintient la note d'archive en tête du fichier racine

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

## ⚠️ RÈGLE CRITIQUE : Audit obligatoire après dev/modif

**Après avoir développé un nouveau tool OU modifié un tool existant, vous DEVEZ suivre la méthodologie d'audit complète (voir `# 🔍 MÉTHODOLOGIE AUDIT TOOLS.txt`)**

**Sélection du tool à auditer**
- Priorité: si un tool vient d'être développé ou modifié, il est audité en priorité (audit direct de ce tool).
- Sinon: sélectionner aléatoirement parmi les « Tools restants » via l'outil `random` (opération `pick_random`).
- Cas trivial: s'il ne reste qu'un tool, la sélection est directe (pas de tirage).

Cela inclut:
1. Tests préliminaires (5 tests baseline)
2. Audit JSON spec + code
3. Correctifs si nécessaire
4. Tests validation
5. Tests non-régression OBLIGATOIRES
6. CHANGELOG
7. Commit + push
8. MAJ procédure

**Pourquoi** : garantir que chaque tool respecte les invariants du guide et éviter les régressions.

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
- [ ] NE PAS éditer `src/tools/README.md` à la main — lancer `scripts/generate_tools_catalog.py` (déjà appelé par `scripts/dev.*`) et committer le résultat
- [ ] **Fichiers < 7KB ou 250 lignes** (découper si nécessaire)
- [ ] **Code mort supprimé** : débusquer et supprimer les fonctions/classes/imports non utilisés (avec prudence, vérifier dépendances)

---

## Audit : débusquer le code mort

Lors d'un audit, **traquer et supprimer le code non utilisé** (avec prudence) :

### Indicateurs de code mort

- Fonctions/méthodes jamais appelées
- Imports inutilisés
- Variables définies mais jamais lues
- Fichiers legacy (ex: `tool_execution.py`, `mcp_tools.py` dupliqués)
- Blocs commentés (si > 50 lignes)
- Constantes/config inutilisées

### Méthodologie

1. **Vérifier les imports** : outil `pylint --disable=all --enable=unused-import` ou analyse manuelle
2. **Grep les usages** : chercher les références dans le codebase avant suppression
3. **Tests de régression** : après suppression, re-tester toutes les fonctionnalités
4. **Commit distinct** : `refactor(tool): remove dead code (X bytes saved)`

### Exemples courants

```python
# ❌ Import non utilisé
import requests  # si jamais appelé → supprimer

# ❌ Fonction orpheline
def old_helper():  # si aucun appel → supprimer
    pass

# ❌ Legacy wrapper
# def old_api():  # code commenté depuis 6 mois → supprimer
#     return new_api()

# ❌ Doublon
# Si tool_execution.py et tools_exec.py font la même chose → garder 1 seul
```

### Prudence

- **Ne jamais supprimer** les exports publics (`__all__`) sans vérifier les imports externes
- **Garder** les helpers utilisés dans les tests (même si absents du code principal)
- **Documenter** dans le commit message pourquoi le code était mort

---

## Découpage des fichiers volumineux (> 7KB)

### Règle

**Aucun fichier Python ne doit dépasser 7KB ou 250 lignes** (facilite maintenance et review).

### Stratégie de découpage

**Exemple : `streaming.py` (19KB) → découper en :**
- `streaming_sse.py` — parsing SSE (flags, extract, stats)
- `streaming_media.py` — extraction media multimodal
- `streaming_fallback.py` — fallback non-SSE (JSON once)
- `streaming.py` — orchestrateur principal (imports les 3)

**Exemple : `core.py` (10KB) → extraire :**
- `usage_utils.py` — merge usage cumulatif
- `vision_utils.py` — helpers images (data URL, chroot)

### Organisation cohérente

```
_tool_name/
  ├── api.py          # Routes publiques (< 7KB)
  ├── core.py         # Logique métier principale (< 7KB)
  ├── validators.py   # Validations pures (< 7KB)
  ├── utils.py        # Helpers génériques (< 7KB)
  ├── streaming/      # Si streaming complexe
  │   ├── sse.py
  │   ├── media.py
  │   └── fallback.py
  └── services/       # I/O externes
      ├── http.py
      └── db.py
```

**Principe** : 1 fichier = 1 responsabilité claire. Si > 7KB → découper logiquement.

---

## Exemple audit complet (résumé)

**Outil audité** : `telegram_bot`

**Problèmes détectés** :
- 🔴 Token exposé dans erreurs → masking ajouté
- 🟡 Pas de truncation warning → ajouté
- 🟢 Logging manquant → ajouté

**Score** : 7.7 → 9.2/10 ⭐⭐⭐⭐⭐

**Tests non-régression** : 10/10 OK

**Commit** :
```
fix(telegram_bot): critical audit fixes (7.7→9.2/10)

🔴 SECURITY: token masking in errors
🟡 MAJOR: truncation warnings, counts
🟢 IMPROVEMENTS: logging (INFO/WARNING)

TECHNICAL: conformité 75%→98%
TESTS: 10/10 non-régression OK
```

---

## Résumé des règles absolues

1. **Audit obligatoire** après tout dev/modif de tool. Sélection: audit prioritaire du tool modifié; sinon tirage aléatoire parmi les tools restants; s'il n'en reste qu'un, sélection directe.
2. **Fichiers < 7KB** (découper si nécessaire)
3. **Code mort supprimé** (avec prudence)
4. **Specs JSON** = source de vérité (ne jamais dupliquer en Python)
5. **Tests non-régression OBLIGATOIRES** avant tout commit
6. **Outputs minimaux** (pas de metadata verbose)
7. **Truncation warnings** si > 50 items
8. **Logging** (INFO/WARNING/ERROR) pour debug production
9. **CHANGELOG** condensé (essentiel uniquement)
10. **Commit atomique** : 1 tool à la fois, message structuré
