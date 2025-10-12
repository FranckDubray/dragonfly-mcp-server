# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [1.22.0] - 2025-10-12

### Added
- **ssh_admin**: Nouveau tool administration serveurs SSH
  - 4 opérations: connect, exec, upload, download
  - **Authentification SSH keys UNIQUEMENT** (pas de passwords)
  - Chroot sécurisé: clés dans `ssh_keys/` relatif à la racine projet
  - Support multi-serveurs via profils JSON (.env)
  - Audit logging complet dans `sqlite3/ssh_audit.db`
  - Output truncation (10KB max) pour protection contexte LLM
  - Path traversal protection stricte
  - Support RSA, ED25519, ECDSA keys
  - Passphrase optionnel pour clés protégées
  - Transfert fichiers via SCP (upload/download)
  - Execution commandes/scripts bash (1 ligne ou multi-lignes)
  - Timeouts configurables (défaut: 30s connexion, 30s exec)

### Technical Details
- Nouveau package: `src/tools/_ssh_admin/`
  - client.py: SSH client wrapper (paramiko)
  - profiles.py: Gestion profils .env
  - ops_basic.py: connect + exec
  - ops_transfer.py: upload + download (SCP/SFTP)
  - logger.py: Audit trail SQLite
  - utils.py: Helpers (path resolution, truncation)
  - operations.py: Router principal
- Spec: src/tool_specs/ssh_admin.json
- Bootstrap: src/tools/ssh_admin.py
- Structure: `ssh_keys/` à la racine (comme sqlite3/)
- Dépendance: paramiko>=3.4.0
- Total: ~700 lignes de code
- Category: utilities
- Tags: system, admin, ssh, devops

### Security
- SSH keys exclusivement (passwords interdits)
- Chroot strict: chemins relatifs uniquement
- Path traversal validation
- Permissions check (warning si trop permissif)
- Audit complet: toutes connexions/commandes loguées
- .gitignore: ssh_keys/* protégé (sauf .gitkeep et README)

### Configuration (.env)
```bash
# Profils serveurs (chemins RELATIFS)
SSH_PROFILES_JSON='{"prod": {"host": "server.com", "port": 22, "user": "admin", "key_path": "ssh_keys/id_rsa_prod"}}'

# Timeouts (optionnel)
SSH_CONNECT_TIMEOUT=10
SSH_EXEC_TIMEOUT=30
```

### Usage Examples
```python
# Test connexion
ssh_admin(operation="connect", profile="prod")

# Commande simple
ssh_admin(operation="exec", profile="prod", command="uptime")

# Script multi-lignes
ssh_admin(operation="exec", profile="prod", command="uptime\nfree -m\ndf -h")

# Upload fichier
ssh_admin(operation="upload", profile="prod", local_path="backup.tar.gz", remote_path="/tmp/backup.tar.gz")

# Download log
ssh_admin(operation="download", profile="prod", remote_path="/var/log/nginx/error.log", local_path="logs/nginx.log")
```

---

## [1.21.1] - 2025-10-12

### Improved
- **discord_bot**: Massively reduced output verbosity
  - Default limit reduced from 20 to **5 messages** (max remains 50)
  - Aggressive cleaning of null/useless fields (banner, accent_color, avatar_decoration_data, collectibles, display_name_styles, public_flags, flags, components, placeholder, content_scan_version, etc.)
  - Removed empty arrays and null values from response
  - Cleaned user objects: only id, username, global_name, avatar, bot, discriminator (if != "0")
  - Cleaned attachments: only filename, size, url, content_type, width, height
  - Cleaned reactions: only emoji name + count (no burst/me flags)
  - Cleaned threads: only id, name, message_count
  - **Impact**: Output size reduced by ~60-70% for typical messages
  - **Rationale**: Protect LLM context from flooding with metadata noise

### Technical Details
- utils.py: New `_remove_null_fields()` recursive cleaner
- ops_messages.py: `limit` default changed from 20 to 5
- All cleaning functions rewritten for maximum efficiency
- Backward compatible: All essential data preserved

---

## [1.21.0] - 2025-10-12

### Added
- **discord_bot**: Nouveau tool complet (29 opérations)
  - Client REST Discord Bot API avec authentification token
  - 8 ops messages: list/get/send/edit/delete/bulk_delete/pin/unpin
  - 5 ops channels: list/get/create/modify/delete
  - 3 ops reactions: add/remove/get_reactions
  - 5 ops threads: create/list/join/leave/archive
  - 8 ops utility: list_guilds/search/guild_info/members/permissions/user/emojis/health_check
  - Rate limiting automatique (429 + 5xx retry)
  - Pagination support (before/after/around)
  - Search local avec filtres (content/author/date)
  - Health check endpoint pour validation token
  - Documentation spec JSON complète

### Fixed
- **discord_bot**: Protection LLM context overflow
  - list_messages: limite par défaut 20 messages (était 50)
  - list_messages: limite max 50 messages (était 100)
  - Évite le flood du contexte LLM avec historiques massifs

### Known Limitations
- **discord_bot**: MESSAGE_CONTENT Intent requis
  - Sans cet intent privilégié, les messages retournent `content: ""` et `embeds: []`
  - Configuration requise : Developer Portal → Bot → Privileged Gateway Intents → Message Content Intent
  - Propagation : peut prendre 2-10 minutes après activation
  - Approbation Discord requise si bot sur ≥100 serveurs
  - Exceptions (content visible sans intent) : messages du bot lui-même, DMs, messages mentionnant le bot

### Technical Details
- Nouveau package: `src/tools/_discord_bot/`
  - client.py: HTTP client avec rate limiting
  - utils.py: Helpers (snowflake conversion, datetime parsing)
  - ops_messages.py: 8 opérations messages
  - ops_channels.py: 5 opérations channels
  - ops_reactions.py: 3 opérations reactions
  - ops_threads.py: 5 opérations threads
  - ops_utility.py: 8 opérations utility
  - operations.py: Router principal (29 ops)
- Spec: src/tool_specs/discord_bot.json (6.2 Ko)
- Bootstrap: src/tools/discord_bot.py
- Total: ~15 Ko de code
- Requis: DISCORD_BOT_TOKEN dans .env
- Compatible: Tous serveurs Discord où le bot a les permissions
- Multi-channel: Accès à tous les salons (vs webhook = 1 canal fixe)

---

## [1.20.0] - 2025-10-12

### Added
- **discord_webhook**: Support threads Discord (Phase 1 - Quick wins)
  - Nouveau paramètre `thread_id` (pattern: `^[0-9]{17,20}$`)
  - Posting dans threads existants via query param `?thread_id=xxx`
  - Compatible create/update/upsert/delete
  - Documentation complète dans la spec JSON

- **discord_webhook**: Opération READ complète (Phase 2 - Priority)
  - Récupération messages Discord via webhook API
  - 4 modes: `message_id` (single), `message_ids` (batch max 50), `article_key` (from store), `article_key + message_id`
  - Options avancées:
    - `include_metadata` (default: true): reactions, mentions, attachments metadata, timestamps
    - `parse_embeds` (default: true): structure détaillée vs brut
    - `thread_id`: contexte thread optionnel
  - Retour structuré: messages[], count, errors[] (si partial fail)
  - Gestion erreurs: 404, 502, partial success avec détails
  - Rate limit aware (retry 429 automatique)

### Fixed
- **discord_webhook**: Rate limiting Discord (CRITIQUE)
  - Implémentation retry automatique sur 429 Too Many Requests
  - Respect du `retry_after` renvoyé par Discord (cap à 30s max)
  - Exponential backoff sur erreurs 5xx (0.25s → 0.5s → 1.0s)
  - Max 3 tentatives avec fallback gracieux
  - Appliqué à http_request() ET http_request_multipart()

### Improved
- **discord_webhook**: Validation attachments (robustesse)
  - Contrôle strict 25 Mo par fichier (erreur explicite avec taille en MB)
  - Contrôle 25 Mo total par message
  - Validation en amont (upload_image_url ET attachments base64)
  - Messages d'erreur détaillés : `"'{filename}' is too large (XX.XX MB). Discord limit: 25 MB per file."`

### Known Limitations
- **discord_webhook**: Discord IDs (snowflakes) precision
  - Les IDs Discord sont des entiers 64-bit qui peuvent dépasser Number.MAX_SAFE_INTEGER JavaScript
  - **Recommandation**: Utiliser `message_ids: ["123"]` (array) au lieu de `message_id: "123"` (scalar)
  - Le mode array préserve les strings et évite les conversions float implicites
  - Documentation ajoutée dans la spec JSON avec warnings explicites

### Technical Details
- ops_read.py: +6.8 Ko (logique read complète)
- http_client.py: +1.5 Ko (retry logic complet)
- attachments.py: +1.3 Ko (size validation)
- ops_create_update.py: +610 bytes (thread_id routing)
- operations.py: +186 bytes (read routing)
- spec: +1.1 Ko (read parameters)
- Total impact: ~11.5 Ko, 0 breaking changes
- Backward compatible : tous nouveaux paramètres optionnels
- Tests manuels : OK (create avec thread_id, read modes, retry 429 simulé)

---

## [1.19.0] - 2025-10-12

### Fixed
- **generate_edit_image**: Critical fix for stream mode handling
  - Fixed 404 error caused by inconsistent payload (stream=true with non-streaming request)
  - `_single_call()` now explicitly sets stream=false for non-stream attempts
  - Fallback correctly uses stream=true as expected by backend
  - Both generate and edit operations now work reliably

### Added
- **generate_edit_image**: Local file support for image inputs (completed)
  - New `image_files` parameter: accepts local image paths relative to `./docs`
  - Examples: `"test.png"`, `"images/photo.jpg"`, `"subdir/image.webp"`
  - Supports PNG, JPEG, WebP with automatic MIME type detection
  - Can be combined with `images` parameter (URLs/data URLs) — max 3 total
  - Intelligent path resolution using same strategy as `call_llm`
  - Security: Path traversal protection (chroot to ./docs)
  - Optional `DOCS_ABS_ROOT` env var override

### Changed
- **Changelog management**: Implemented rotation policy
  - Archived versions 1.14.3 to 1.18.2 in `changelogs/CHANGELOG_1.14.3_to_1.18.2.md`
  - Root CHANGELOG.md now contains only latest release (1.19.0)
  - Follows LLM_DEV_GUIDE archival strategy (keep latest 10 versions at root)

### Technical Details
- generate_edit_image: validators.py enhanced with local file loading
  - `load_local_images()`: reads files from ./docs and converts to data URLs
  - `_get_docs_root()`: intelligent project root detection
  - Path resolution: `Path(__file__).parent.parent.parent.parent / "docs"`
  - Error handling: clear messages for missing files, path traversal attempts
- Total improvements since 1.18.0:
  - Code complexity reduced by 36% (403 → 259 lines in core.py)
  - Debug payload reduced by 80% (40KB → 8KB)
  - 3 input types supported: local files, URLs, data URLs/base64
  - Backward compatible with all existing integrations

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).
