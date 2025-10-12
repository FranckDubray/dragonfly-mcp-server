# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [1.22.1] - 2025-10-12

### Added
- **ssh_admin**: Nouvelle opération `exec_file` pour exécuter scripts bash locaux
  - Lit un script bash local (ex: `scripts/deploy.sh`)
  - L'exécute sur le serveur distant via SSH
  - Support arguments (`args` array) passés comme $1, $2, etc
  - Chemins relatifs à la racine projet (chroot)
  - Validation fichier existe + path traversal protection
  - Escaping automatique des arguments pour shell safety
  - Output truncation (10KB) + audit logging

### Technical Details
- ops_basic.py: nouvelle fonction `op_exec_file()`
- operations.py: routing `exec_file`
- Spec JSON: ajout `exec_file` dans enum + paramètres `script_path` et `args`
- Exemples: `scripts/example_ssh_health_check.sh` et `scripts/example_ssh_service_check.sh`
- Documentation: `scripts/README.md` avec best practices

### Usage Examples
```python
# Script simple
ssh_admin(operation="exec_file", profile="prod", script_path="scripts/health_check.sh")

# Script avec arguments
ssh_admin(operation="exec_file", profile="prod", 
         script_path="scripts/service_check.sh", 
         args=["nginx", "postgresql"])
```

### Use Cases
- Déploiement applications (scripts de deploy)
- Monitoring système (health checks)
- Maintenance serveurs (cleanup, backups)
- Configuration management (setup scripts)
- Troubleshooting (diagnostic scripts)

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

For older versions, see: [changelogs/](changelogs/) (range-based archives).
