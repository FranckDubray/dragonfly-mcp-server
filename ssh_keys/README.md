# SSH Keys Directory

Ce répertoire contient les clés SSH privées pour l'authentification serveur.

## ⚠️ SÉCURITÉ CRITIQUE

- **NE JAMAIS** commiter de clés privées dans Git
- Permissions recommandées : `chmod 600 id_rsa_*`
- Clés protégées par passphrase recommandé

## 📋 Setup

1. Copier vos clés SSH ici :
   ```bash
   cp ~/.ssh/id_rsa_prod ssh_keys/
   chmod 600 ssh_keys/id_rsa_prod
   ```

2. Configurer `.env` avec chemins relatifs :
   ```json
   SSH_PROFILES_JSON='{"prod": {"host": "server.com", "port": 22, "user": "admin", "key_path": "ssh_keys/id_rsa_prod"}}'
   ```

## 🔑 Génération clés

```bash
# RSA 4096 bits
ssh-keygen -t rsa -b 4096 -f ssh_keys/id_rsa_prod -C "prod-server"

# ED25519 (recommandé, plus sécurisé)
ssh-keygen -t ed25519 -f ssh_keys/id_ed25519_prod -C "prod-server"
```

## 📂 Structure

- `id_rsa_*` : Clés privées RSA
- `id_ed25519_*` : Clés privées ED25519
- `*.pub` : Clés publiques (peuvent être commitées)
- `known_hosts` : Fingerprints serveurs validés (optionnel)

## 🔒 Sécurité

Tous les chemins dans `.env` doivent être **relatifs** à la racine du projet :
- ✅ BON : `"key_path": "ssh_keys/id_rsa_prod"`
- ❌ MAUVAIS : `"key_path": "/home/user/.ssh/id_rsa"`

Le tool refuse les chemins absolus et valide la traversée de répertoire.
