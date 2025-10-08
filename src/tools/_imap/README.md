# IMAP Email Tool

Accès universel aux emails via le protocole IMAP standard (Gmail, Outlook, Yahoo, iCloud, Infomaniak, serveurs custom).

## Pourquoi IMAP ?

- **Protocole universel** : tous les providers le supportent (vs API REST propriétaires)
- **Setup rapide** : 5 minutes (vs 30+ minutes pour OAuth/GCP)
- **Pas de config cloud** : pas besoin de projet GCP, consent screen, etc.
- **Multi-comptes** : gérez plusieurs boîtes email simultanément (Gmail + Infomaniak + Outlook...)
- **Secure** : App Passwords recommandés (2FA)

---

## ⚙️ Configuration multi-comptes

Les credentials sont stockés dans **`.env`** (à la racine du projet) ou configurables via **`/config`**.

### Variables d'environnement par provider

```bash
# Gmail (compte 1)
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=abcdefghijklmnop  # App Password (pas d'espaces)

# Infomaniak (compte 2)
IMAP_INFOMANIAK_EMAIL=contact@votredomaine.com
IMAP_INFOMANIAK_PASSWORD=votre_password

# Outlook/Hotmail (compte 3)
IMAP_OUTLOOK_EMAIL=user@outlook.com
IMAP_OUTLOOK_PASSWORD=votre_password

# Yahoo (compte 4)
IMAP_YAHOO_EMAIL=user@yahoo.com
IMAP_YAHOO_PASSWORD=app_password

# iCloud (compte 5)
IMAP_ICLOUD_EMAIL=user@icloud.com
IMAP_ICLOUD_PASSWORD=app_specific_password

# Custom server (compte 6)
IMAP_CUSTOM_EMAIL=user@company.com
IMAP_CUSTOM_PASSWORD=password
IMAP_CUSTOM_SERVER=mail.company.com
IMAP_CUSTOM_PORT=993
IMAP_CUSTOM_USE_SSL=true
```

### Configuration via l'interface `/config`

1. Ouvre **http://127.0.0.1:8000/control**
2. Section **Configuration**
3. Ajoute les variables ci-dessus pour chaque compte
4. Save

---

## 🔐 Setup rapide Gmail (5 minutes)

### Étape 1 : Activer la 2FA (si pas déjà fait)

1. **[myaccount.google.com/security](https://myaccount.google.com/security)**
2. **"Validation en deux étapes"** → Activer
3. Suis les instructions (numéro de téléphone)

### Étape 2 : Générer un App Password

1. **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**
2. Sélectionne **"Autre (nom personnalisé)"** → Entre **"Dragonfly MCP"**
3. Clique **Générer**
4. Copie le mot de passe (16 caractères, ex: `abcd efgh ijkl mnop`)

### Étape 3 : Configurer `.env`

```bash
IMAP_GMAIL_EMAIL=ton.email@gmail.com
IMAP_GMAIL_PASSWORD=abcdefghijklmnop  # Enlève les espaces
```

### Étape 4 : Redémarrer le serveur MCP

```bash
./scripts/dev.sh  # ou scripts\dev.ps1 (Windows)
```

---

## 🔐 Setup rapide Infomaniak (2 minutes)

### Étape 1 : Pas de 2FA obligatoire
- Utilisez votre mot de passe email habituel
- Ou générez un mot de passe d'application si disponible

### Étape 2 : Configurer `.env`

```bash
IMAP_INFOMANIAK_EMAIL=contact@votredomaine.com
IMAP_INFOMANIAK_PASSWORD=votre_password
```

### Étape 3 : Redémarrer le serveur

```bash
./scripts/dev.sh
```

---

## 📖 Operations

### `connect` — Tester la connexion
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "connect"
  }
}
```

**Retour :**
```json
{
  "success": true,
  "provider": "gmail",
  "server": "imap.gmail.com",
  "email": "user@gmail.com",
  "folders_count": 15
}
```

---

### `list_folders` — Lister les dossiers
```json
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "list_folders"
  }
}
```

---

### `search_messages` — Rechercher des emails
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "search_messages",
    "folder": "inbox",
    "query": {
      "from": "bob@example.com",
      "unseen": true,
      "since": "2025-10-01"
    },
    "max_results": 20
  }
}
```

**Critères de recherche supportés (`query`) :**
- `from`, `to`, `subject`, `text` (string)
- `since`, `before` (date YYYY-MM-DD)
- `unseen`, `seen`, `flagged` (boolean)

---

### `get_message` — Récupérer un email complet
```json
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "get_message",
    "message_id": "12345",
    "folder": "inbox",
    "include_body": true,
    "include_attachments_metadata": true
  }
}
```

---

### `download_attachments` — Télécharger les pièces jointes
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "download_attachments",
    "message_id": "12345",
    "folder": "inbox",
    "output_dir": "files/imap/attachments/12345"
  }
}
```

---

### `mark_read` / `mark_unread` — Marquer comme lu/non-lu
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "mark_read",
    "message_id": "12345",
    "folder": "inbox"
  }
}
```

---

### `mark_read_batch` / `mark_unread_batch` — Opérations batch
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "mark_read_batch",
    "message_ids": ["12345", "12346", "12347"],
    "folder": "inbox"
  }
}
```

---

### `move_message` — Déplacer vers un autre dossier
```json
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "move_message",
    "message_id": "12345",
    "folder": "inbox",
    "target_folder": "Work"
  }
}
```

---

### `mark_spam` — Marquer comme spam (batch)
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "mark_spam",
    "message_ids": ["12345", "12346", "12347"],
    "folder": "inbox"
  }
}
```

---

### `delete_message` — Supprimer un email
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "delete_message",
    "message_id": "12345",
    "folder": "inbox",
    "expunge": true
  }
}
```

---

## 🌐 Providers supportés

### Gmail
```bash
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=abcdefghijklmnop  # App Password obligatoire si 2FA
```
- **Server:** `imap.gmail.com:993` (SSL)
- **Folders spéciaux:** `[Gmail]/Sent Mail`, `[Gmail]/Trash`, `[Gmail]/All Mail`
- **IMAP activé par défaut** depuis janvier 2025

### Outlook / Hotmail / Live.com / Office365
```bash
IMAP_OUTLOOK_EMAIL=user@outlook.com
IMAP_OUTLOOK_PASSWORD=votre_password
```
- **Server:** `outlook.office365.com:993` (SSL)
- **Folders:** `Sent`, `Deleted`, `Junk`

### Yahoo Mail
```bash
IMAP_YAHOO_EMAIL=user@yahoo.com
IMAP_YAHOO_PASSWORD=abcdefghijklmnop  # App Password OBLIGATOIRE
```
- **Server:** `imap.mail.yahoo.com:993` (SSL)
- **App Password requis** : Account Security → Generate app password

### iCloud Mail
```bash
IMAP_ICLOUD_EMAIL=user@icloud.com
IMAP_ICLOUD_PASSWORD=abcd-efgh-ijkl-mnop  # App-specific password
```
- **Server:** `imap.mail.me.com:993` (SSL)
- **App-specific password** : Apple ID → Security → App-Specific Passwords

### Infomaniak
```bash
IMAP_INFOMANIAK_EMAIL=contact@votredomaine.com
IMAP_INFOMANIAK_PASSWORD=votre_password
```
- **Server:** `mail.infomaniak.com:993` (SSL)
- **Folders:** `INBOX`, `Sent`, `Trash`, `Junk`, `Drafts`
- **Swiss cloud provider** : utilisez votre email complet + password (ou App Password si disponible)

### Custom (serveur entreprise / self-hosted)
```bash
IMAP_CUSTOM_EMAIL=user@company.com
IMAP_CUSTOM_PASSWORD=votre_password
IMAP_CUSTOM_SERVER=mail.company.com
IMAP_CUSTOM_PORT=993
IMAP_CUSTOM_USE_SSL=true
```

---

## 📁 Alias de dossiers

Le tool normalise automatiquement les alias courants :

| Alias | Gmail | Outlook | Yahoo | iCloud | Infomaniak |
|-------|-------|---------|-------|--------|------------|
| `inbox` | INBOX | INBOX | INBOX | INBOX | INBOX |
| `sent` | [Gmail]/Sent Mail | Sent | Sent | Sent Messages | Sent |
| `trash` | [Gmail]/Trash | Deleted | Trash | Deleted Messages | Trash |
| `spam` | [Gmail]/Spam | Junk | Bulk Mail | Junk | Junk |

Utilisez les alias (`"folder": "sent"`) pour un code portable.

---

## 🔄 Utilisation multi-comptes

### Exemple : Gérer Gmail ET Infomaniak simultanément

**1. Configuration `.env`**
```bash
# Compte Gmail personnel
IMAP_GMAIL_EMAIL=perso@gmail.com
IMAP_GMAIL_PASSWORD=gmail_app_password

# Compte Infomaniak professionnel
IMAP_INFOMANIAK_EMAIL=contact@entreprise.com
IMAP_INFOMANIAK_PASSWORD=infomaniak_password
```

**2. Lire emails Gmail**
```json
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "search_messages",
    "folder": "inbox",
    "query": {"unseen": true}
  }
}
```

**3. Lire emails Infomaniak**
```json
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "search_messages",
    "folder": "inbox",
    "query": {"unseen": true}
  }
}
```

**4. Déplacer un email Infomaniak vers un dossier**
```json
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "move_message",
    "message_id": "789",
    "folder": "inbox",
    "target_folder": "Clients"
  }
}
```

---

## 🔒 Sécurité

✅ **App Passwords recommandés** : ne jamais utiliser le mot de passe principal du compte  
✅ **Stockage sécurisé** : passwords dans `.env` (masked en logs, ignoré par Git)  
✅ **SSL par défaut** : connexions chiffrées (port 993)  
✅ **Chroot projet** : attachments sauvés sous `files/imap/` uniquement  
✅ **Aucun credential en paramètre d'appel** : tout est lu depuis `.env` via le `provider`

---

## ❌ Troubleshooting

### "IMAP_GMAIL_EMAIL not configured"
- Ajoute `IMAP_GMAIL_EMAIL=ton.email@gmail.com` dans `.env`
- Ou configure via `/config`

### "IMAP_INFOMANIAK_PASSWORD not configured"
- Ajoute `IMAP_INFOMANIAK_PASSWORD=...` dans `.env`

### "Authentication failed"
- ✅ Vérifie que la 2FA est activée (Gmail/Yahoo/iCloud)
- ✅ Régénère un nouveau App Password
- ✅ Pas d'espaces dans le password (`.env` : `abcdefghijklmnop`)
- ✅ Pour Infomaniak : utilisez votre mot de passe email habituel

### "Failed to select folder"
- Liste les folders avec `list_folders` pour voir les noms exacts
- Utilise les alias (`inbox`, `sent`, `trash`)

---

## 🧪 Test rapide multi-comptes

```bash
# 1. Configure .env avec Gmail ET Infomaniak
echo "IMAP_GMAIL_EMAIL=perso@gmail.com" >> .env
echo "IMAP_GMAIL_PASSWORD=gmail_app_password" >> .env
echo "IMAP_INFOMANIAK_EMAIL=contact@entreprise.com" >> .env
echo "IMAP_INFOMANIAK_PASSWORD=infomaniak_password" >> .env

# 2. Redémarre le serveur
./scripts/dev.sh

# 3. Test connexion Gmail
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"tool":"imap","params":{"provider":"gmail","operation":"connect"}}'

# 4. Test connexion Infomaniak
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"tool":"imap","params":{"provider":"infomaniak","operation":"connect"}}'

# 5. Liste emails Gmail non lus
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"tool":"imap","params":{"provider":"gmail","operation":"search_messages","folder":"inbox","query":{"unseen":true},"max_results":5}}'

# 6. Liste emails Infomaniak non lus
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"tool":"imap","params":{"provider":"infomaniak","operation":"search_messages","folder":"inbox","query":{"unseen":true},"max_results":5}}'
```

---

Pour toute question : voir **LLM_DEV_GUIDE.md** ou **README** racine du projet.
