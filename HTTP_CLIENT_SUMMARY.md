# Tool HTTP Client - Résumé pour mise à jour des README

## 📊 Informations clés

**Nom du tool :** `http_client`  
**Nombre total de tools :** 18 (était 17 avant)  
**Catégorie :** 🌐 Réseau & API

---

## 📝 Description courte (pour README principal)

**http_client** — Client HTTP/REST universel pour interagir avec n'importe quelle API. Supporte tous les méthodes (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS), authentification (Basic, Bearer, API Key), retry automatique avec backoff exponentiel, timeout, proxy, et parsing intelligent des réponses.

---

## 🎯 Architecture

- **Bootstrap** : `src/tools/http_client.py`
- **Package** : `src/tools/_http_client/` (api, core, auth, retry, validators, utils)
- **Spec canonique** : `src/tool_specs/http_client.json`
- **Saves** : `files/http_responses/` (optionnel, chroot projet)

---

## 🔧 Fonctionnalités

### HTTP Methods
- GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

### Authentication
- **Basic Auth** : username + password
- **Bearer Auth** : JWT/token
- **API Key** : custom header

### Body Formats
- JSON (auto-serialized avec Content-Type)
- Form data (application/x-www-form-urlencoded)
- Raw text/XML

### Advanced Features
- **Retry logic** : exponential backoff (0-5 retries)
- **Timeout** : configurable (1-300s, default 30s)
- **Proxy** : HTTP/HTTPS/SOCKS5
- **SSL verification** : toggle on/off
- **Response parsing** : auto-detect, JSON, text, raw
- **Save responses** : optional file storage
- **Follow redirects** : configurable

---

## 💡 Exemples rapides

### Simple GET
```json
{
  "method": "GET",
  "url": "https://api.github.com/users/octocat"
}
```

### POST avec JSON + Bearer Auth
```json
{
  "method": "POST",
  "url": "https://api.example.com/data",
  "json": {"key": "value"},
  "auth_type": "bearer",
  "auth_token": "your_token_here"
}
```

### GET avec retry
```json
{
  "method": "GET",
  "url": "https://api.example.com/unstable",
  "max_retries": 3,
  "retry_delay": 2.0,
  "timeout": 10
}
```

### API Key Auth
```json
{
  "method": "GET",
  "url": "https://api.example.com/data",
  "auth_type": "api_key",
  "auth_api_key_name": "X-API-Key",
  "auth_api_key_value": "secret_key"
}
```

---

## 📊 Format de réponse

### Succès
```json
{
  "success": true,
  "status_code": 200,
  "headers": {...},
  "ok": true,
  "body": {...},
  "body_length": 1234,
  "request": {
    "method": "GET",
    "url": "..."
  }
}
```

### Erreur
```json
{
  "error": "Request timed out after 30 seconds",
  "error_type": "timeout"
}
```

**Types d'erreurs :**
- `timeout` : dépassement timeout
- `connection` : échec connexion
- `ssl` : erreur certificat SSL
- `request` : erreur générique requête
- `unknown` : erreur inattendue

---

## 🔐 Sécurité

✅ Validation URL (http/https uniquement)  
✅ Timeout obligatoire (évite hang infini)  
✅ SSL verification par défaut  
✅ Auth credentials masquées dans logs  
✅ Chroot saves : `files/http_responses/`  
✅ Pas d'exécution de code arbitraire  

---

## 🎨 Section README à ajouter

### Pour `/README.md` (section Outils)

Ajouter dans **Réseau & API** :

```markdown
### 🌐 Réseau & API

#### **http_client** — Client HTTP/REST universel ⭐
- **Toutes les méthodes** : GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Auth** : Basic, Bearer, API Key
- **Body formats** : JSON, form-data, raw
- **Retry automatique** : exponential backoff (0-5 tentatives)
- **Timeout** : configurable (1-300s)
- **Proxy** : HTTP/HTTPS/SOCKS5
- **SSL** : verification toggle
- **Response parsing** : auto-detect, JSON, text, raw
- **Save responses** : optionnel vers files/
- Architecture : `_http_client/` (api, core, auth, retry, validators, utils)
```

---

## 🎯 Use Cases

1. **Tester des APIs** : valider endpoints REST
2. **Webhooks** : envoyer des callbacks
3. **Intégrations** : Stripe, Twilio, Slack, etc.
4. **Monitoring** : health checks avec retry
5. **Data fetching** : récupérer des données JSON
6. **Authentification** : tester JWT/Bearer/API keys
7. **Proxy testing** : via corporate proxies
8. **SSL debugging** : toggle verification pour dev

---

## ✅ Checklist

- [x] Tool créé avec architecture modulaire
- [x] Spec JSON complète et validée
- [x] Tous les types d'auth (Basic, Bearer, API Key)
- [x] Retry avec exponential backoff
- [x] Timeout configurable
- [x] Proxy support
- [x] SSL verification toggle
- [x] Response parsing intelligent
- [x] Save to file optionnel
- [x] Validation complète des inputs
- [x] Error handling exhaustif
- [x] Documentation complète (README)
- [ ] Tests manuels (après reload serveur)
- [ ] README racine mis à jour
- [ ] CHANGELOG mis à jour
- [ ] Release v1.6.0

---

**Tool production-ready après tests ! 🚀**
