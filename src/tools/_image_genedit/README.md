# generate_edit_image — Gemini Image Studio

Génération et édition d'images via gemini-2.5-flash-image-preview.

## Architecture

```
generate_edit_image.py        # Bootstrap (run + spec)
_image_genedit/
  ├── __init__.py              # Exports
  ├── core.py                  # Entry point (run_image_op)
  ├── operations.py            # API calls (_single_call, _sequential_fallback)
  ├── client.py                # HTTP client (headers, timeouts, SSL)
  ├── payloads.py              # Message builders (generate, edit)
  ├── streaming.py             # SSE parsing + URL extraction
  ├── validators.py            # Input validation + normalization
  ├── utils.py                 # Helpers (URL extraction, downloads)
  └── README.md                # This file
```

## Operations

### 1. generate
Génère des images à partir d'un prompt texte.

**Params**:
- `prompt` (str, required): Description de l'image
- `n` (int, default: 1, max: 8): Nombre de variations

**Example**:
```json
{
  "operation": "generate",
  "prompt": "A futuristic city at sunset",
  "n": 4
}
```

### 2. edit
Édite des images existantes selon un prompt.

**Params**:
- `prompt` (str, required): Instructions d'édition
- `images` (list[str], 1-3): URLs http(s), data URLs, ou base64 brut
- `image_files` (list[str], 1-3): Fichiers locaux (paths relatifs à ./docs)
- `n` (int, default: 1, max: 8): Nombre de variations

**Example**:
```json
{
  "operation": "edit",
  "prompt": "Add a blue sky",
  "image_files": ["gemini_image_68dfaca1489e1.png"],
  "n": 2
}
```

**Notes**:
- `images` et `image_files` peuvent être combinés (max 3 total)
- Fichiers locaux: sécurité chroot (./docs uniquement)
- HTTP(S) images: téléchargées et converties en data URLs

## Input Formats

**Supported**:
- `http(s)://...` — Téléchargé automatiquement
- `data:image/...;base64,...` — Utilisé tel quel
- Base64 brut — Wrappé en data URL automatiquement
- Fichiers locaux (via `image_files`) — Chargés depuis ./docs

## Output

```json
{
  "urls": ["https://...", "https://..."],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 3901,
    "total_tokens": 3916,
    "total_token_cost": 39028.75
  },
  "finish_reason": "stop"
}
```

**Notes**:
- Backend produit **toujours** du PNG 1024×1024 (ratio 1:1 fixe)
- Pas de `success` ou `operation` (outputs minimaux, conformité LLM_DEV_GUIDE)

## Timeouts

**Defaults** (configurables via env):
- Single operation: connect=15s, read=180s
- Multi-image edit: connect=30s, read=600s

**Environment overrides**:
```bash
IMAGE_TIMEOUT_SEC=180           # Read timeout (single)
IMAGE_MULTI_TIMEOUT_SEC=600     # Read timeout (multi-edit)
IMAGE_CONNECT_TIMEOUT_SEC=15    # Connect timeout (both)
```

## Fallbacks

1. **Non-stream first**: Try `stream=false` (some backends reject streaming)
2. **Streaming fallback**: Parse SSE if non-stream fails
3. **Sequential fallback**: If batch returns fewer URLs than requested, execute remaining as single calls

## Logging

**Levels**:
- `INFO`: Operations started/completed, files loaded
- `WARNING`: Batch incomplete (sequential fallback), download failures
- `ERROR`: Token missing, API errors, validation failures

**Example**:
```
INFO: Image generation: n=1, prompt=A futuristic city at sunset...
INFO: Image generation completed: 1 URLs returned
```

## Conformity Checklist

- [x] Fichiers < 7KB (core.py: 6.29 KB, operations.py: 4.4 KB)
- [x] Logging (INFO/WARNING/ERROR)
- [x] Outputs minimaux (pas de `success`/`operation`)
- [x] Validation stricte (n: 1-8, images 1-3, paths sécurisés)
- [x] Try-catch global (core.py)
- [x] Timeouts configurables
- [x] additionalProperties: false
- [x] Defaults explicites (n: 1)
- [x] No side-effects import
- [x] Chroot security (./docs)

## Known Issues

None.
