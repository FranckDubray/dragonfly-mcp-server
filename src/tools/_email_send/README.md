# 📧 Email Send Tool

Send emails via SMTP using **Gmail** or **Infomaniak**.

**⚠️ Important** : Ce tool utilise les **mêmes credentials que le tool IMAP** (même BAL, même mot de passe).

---

## 🔐 Configuration

### Variables d'environnement (réutilisées depuis IMAP)

Le tool `email_send` utilise **exactement les mêmes variables** que le tool `imap` :

#### Gmail
```bash
IMAP_GMAIL_EMAIL=ton.email@gmail.com
IMAP_GMAIL_PASSWORD=abcd efgh ijkl mnop  # App Password 16 caractères
```

**Note Gmail** : Le `IMAP_GMAIL_PASSWORD` doit être un **App Password** (pas ton mot de passe Gmail).
- Créer un App Password : https://myaccount.google.com/apppasswords
- Nécessite l'activation de la 2FA sur ton compte Gmail

#### Infomaniak
```bash
IMAP_INFOMANIAK_EMAIL=ton.email@infomaniak.ch
IMAP_INFOMANIAK_PASSWORD=ton_mot_de_passe_email
```

**Note Infomaniak** : Utilise ton mot de passe email classique (celui de webmail.infomaniak.com).

---

## 📡 Serveurs SMTP (hardcodés dans le tool)

Les serveurs SMTP sont **codés en dur** dans le tool (pas besoin de les configurer) :

| Provider | Serveur SMTP | Port | Protocole |
|----------|--------------|------|-----------|
| Gmail | `smtp.gmail.com` | 587 | TLS |
| Infomaniak | `mail.infomaniak.com` | 587 | TLS |

---

## 📋 Opérations disponibles

### 1. `test_connection` - Tester la connexion SMTP

**Exemple Gmail :**
```json
{
  "tool": "email_send",
  "params": {
    "provider": "gmail",
    "operation": "test_connection"
  }
}
```

**Exemple Infomaniak :**
```json
{
  "tool": "email_send",
  "params": {
    "provider": "infomaniak",
    "operation": "test_connection"
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "provider": "gmail",
  "host": "smtp.gmail.com",
  "port": 587,
  "email": "ton.email@gmail.com",
  "message": "SMTP connection successful"
}
```

---

### 2. `send` - Envoyer un email

#### Email texte simple (Gmail)
```json
{
  "tool": "email_send",
  "params": {
    "provider": "gmail",
    "operation": "send",
    "to": ["destinataire@example.com"],
    "subject": "Test email",
    "body": "Ceci est un test d'envoi d'email."
  }
}
```

#### Email HTML avec Infomaniak
```json
{
  "tool": "email_send",
  "params": {
    "provider": "infomaniak",
    "operation": "send",
    "to": ["client@example.com"],
    "subject": "Newsletter mensuelle",
    "body": "<h1>Newsletter</h1><p>Voici les nouveautés du mois.</p>",
    "body_type": "html",
    "from_name": "Newsletter Team"
  }
}
```

#### Email avec CC/BCC et priorité haute
```json
{
  "tool": "email_send",
  "params": {
    "provider": "gmail",
    "operation": "send",
    "to": ["manager@company.com"],
    "cc": ["team@company.com"],
    "bcc": ["archive@company.com"],
    "subject": "[URGENT] Incident production",
    "body": "Un incident critique a été détecté.",
    "priority": "high",
    "reply_to": "support@company.com"
  }
}
```

#### Email avec pièces jointes
```json
{
  "tool": "email_send",
  "params": {
    "provider": "gmail",
    "operation": "send",
    "to": ["client@example.com"],
    "subject": "Votre facture",
    "body": "Veuillez trouver ci-joint votre facture.",
    "attachments": ["docs/invoice.pdf", "docs/logo.png"]
  }
}
```

---

## 📊 Paramètres

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `provider` | string | Non | `gmail` ou `infomaniak` (défaut: `gmail`) |
| `operation` | string | Oui | `test_connection` ou `send` |
| `to` | array | Oui (send) | Liste des destinataires (max 100) |
| `subject` | string | Oui (send) | Objet de l'email (max 500 caractères) |
| `body` | string | Oui (send) | Corps de l'email (texte ou HTML) |
| `body_type` | string | Non | `text` ou `html` (défaut: `text`) |
| `cc` | array | Non | Copie carbone (max 50) |
| `bcc` | array | Non | Copie cachée (max 50) |
| `reply_to` | string | Non | Adresse de réponse |
| `attachments` | array | Non | Chemins des pièces jointes (max 10, 25MB total) |
| `from_name` | string | Non | Nom d'affichage de l'expéditeur |
| `priority` | string | Non | `low`, `normal`, `high` (défaut: `normal`) |

---

## 🔄 Relation avec le tool IMAP

| Tool | Direction | Variables env | Serveurs |
|------|-----------|---------------|----------|
| **imap** | ⬇️ Recevoir | `IMAP_<PROVIDER>_EMAIL`<br>`IMAP_<PROVIDER>_PASSWORD` | imap.gmail.com:993<br>mail.infomaniak.com:993 |
| **email_send** | ⬆️ Envoyer | **Mêmes variables** ☝️ | smtp.gmail.com:587<br>mail.infomaniak.com:587 |

**Avantage** : Une seule configuration pour recevoir (IMAP) et envoyer (SMTP) !

---

## 📈 Limites

| Provider | Emails/jour | Destinataires/email | Taille PJ |
|----------|-------------|---------------------|-----------|
| Gmail | 500 (gratuit) | 100 | 25 MB |
| Infomaniak | Illimité* | 150 | 50 MB |

*Selon le plan Infomaniak

---

## 🔧 Dépannage

### Erreur : "IMAP_GMAIL_EMAIL not found in environment variables"

→ Tu dois configurer les variables IMAP (même si tu n'utilises pas le tool imap)

### Erreur : "Authentication failed" (Gmail)

- ✅ Vérifier que `IMAP_GMAIL_PASSWORD` est un **App Password** (16 caractères)
- ✅ Vérifier que la 2FA est activée sur le compte Gmail
- ❌ Ne PAS utiliser ton mot de passe Gmail classique

### Erreur : "Authentication failed" (Infomaniak)

- ✅ Vérifier que `IMAP_INFOMANIAK_PASSWORD` est correct
- ✅ Vérifier que le compte email est actif sur webmail.infomaniak.com

### Erreur : "Connection timeout"

- Vérifier la connexion internet
- Vérifier que le port 587 n'est pas bloqué par un firewall
- Essayer avec un VPN si le réseau bloque SMTP

---

## 🚀 Exemples avancés

### Envoyer un rapport automatisé (Gmail)
```json
{
  "tool": "email_send",
  "params": {
    "provider": "gmail",
    "operation": "send",
    "to": ["manager@company.com"],
    "subject": "Rapport quotidien - 2025-01-11",
    "body": "<html><body><h2>Rapport quotidien</h2><p>Transactions : <strong>1,234</strong></p><p>CA : <strong>56,789€</strong></p></body></html>",
    "body_type": "html",
    "attachments": ["reports/daily_report.pdf"],
    "priority": "high"
  }
}
```

### Email de notification d'alerte (Infomaniak)
```json
{
  "tool": "email_send",
  "params": {
    "provider": "infomaniak",
    "operation": "send",
    "to": ["admin@company.com"],
    "subject": "[ALERT] High CPU Usage",
    "body": "Le serveur prod-01 a atteint 95% d'utilisation CPU.",
    "priority": "high"
  }
}
```

---

## ✅ Checklist de configuration

### Si tu n'as pas encore configuré IMAP :

**Gmail :**
- [ ] Activer la 2FA sur ton compte Gmail
- [ ] Créer un App Password sur https://myaccount.google.com/apppasswords
- [ ] Ajouter dans `.env` :
  ```bash
  IMAP_GMAIL_EMAIL=ton.email@gmail.com
  IMAP_GMAIL_PASSWORD=abcd efgh ijkl mnop
  ```
- [ ] Tester avec `operation: "test_connection"`

**Infomaniak :**
- [ ] Vérifier que ton compte email est actif
- [ ] Ajouter dans `.env` :
  ```bash
  IMAP_INFOMANIAK_EMAIL=ton.email@infomaniak.ch
  IMAP_INFOMANIAK_PASSWORD=ton_mot_de_passe
  ```
- [ ] Tester avec `operation: "test_connection"`

### Si tu as déjà configuré IMAP :

- [x] Les credentials sont déjà configurés ✅
- [ ] Juste tester email_send avec `operation: "test_connection"`
- [ ] Envoyer un premier email de test

---

## 📚 Ressources

- **Gmail App Passwords** : https://myaccount.google.com/apppasswords
- **Infomaniak Webmail** : https://webmail.infomaniak.com/
- **Tool IMAP** : Voir `src/tools/imap.py` pour recevoir des emails
