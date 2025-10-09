# 🔑 Variables d'environnement — Dragonfly MCP Server

Documentation succincte des variables d'environnement.

---

## 🚀 Quick Start

```bash
# 1. Copier le template
cp .env.example .env

# 2. Remplir les valeurs (tokens, passwords)
nano .env

# 3. Démarrer
./scripts/dev.sh

# 4. Modifier en live via le panneau
# http://127.0.0.1:8000/control → 🔑 Configuration
```

---

## 🔥 Hot-Reload

### ✅ Modifiables en live (effet immédiat, sans restart)

- **LLM** : `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`, `LLM_RETURN_DEBUG`, `LLM_STREAM_TRACE`, `LLM_STREAM_DUMP`, `MCP_URL`
- **Git** : `GITHUB_TOKEN`
- **YouTube** : `YOUTUBE_API_KEY`
- **IMAP** : tous les `IMAP_*_EMAIL`, `IMAP_*_PASSWORD`, `IMAP_CUSTOM_*`
- **Vélib'** : `VELIB_STATION_INFO_URL`, `VELIB_STATION_STATUS_URL`
- **JSON** : `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`, `PY_INT_MAX_STR_DIGITS`
- **Academic** : `ACADEMIC_RS_MAX_ITEMS`, `ACADEMIC_RS_MAX_ABSTRACT_CHARS`, `ACADEMIC_RS_MAX_BYTES`
- **Script** : `SCRIPT_TIMEOUT_SEC`

**Usage** : Modifier via `/control` → Save → effet immédiat au prochain appel tool.

### ⚠️ Nécessitent un restart

- `MCP_HOST`, `MCP_PORT` : bind address du serveur FastAPI
- `LOG_LEVEL` : configuration du logger
- `EXECUTE_TIMEOUT_SEC` : timeout global des tools
- `AUTO_RELOAD_TOOLS` : détection automatique des nouveaux tools

**Pourquoi ?** Lues au démarrage du serveur et figées.

### 🔄 Reload manuel

- **URL parameter** : `GET /tools?reload=1` → force le reload des tools
- Utile pour tester un nouveau tool sans restart

---

## 📚 Variables par catégorie

### 🌐 Serveur

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `MCP_HOST` | string | `127.0.0.1` | Adresse d'écoute du serveur |
| `MCP_PORT` | integer | `8000` | Port d'écoute |
| `LOG_LEVEL` | string | `INFO` | Niveau de log (DEBUG, INFO, WARNING, ERROR) |
| `EXECUTE_TIMEOUT_SEC` | integer | `300` | Timeout d'exécution des tools (secondes) |
| `AUTO_RELOAD_TOOLS` | boolean | `1` | Détection auto des nouveaux tools |

### 🤖 LLM Orchestration

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `AI_PORTAL_TOKEN` | secret | — | Token d'authentification AI Portal |
| `LLM_ENDPOINT` | string | — | URL endpoint LLM custom |
| `LLM_REQUEST_TIMEOUT_SEC` | integer | `300` | Timeout requêtes LLM |
| `LLM_RETURN_DEBUG` | boolean | `0` | Inclure debug dans réponses |
| `LLM_STREAM_TRACE` | boolean | `0` | Tracer événements SSE |
| `LLM_STREAM_DUMP` | boolean | `0` | Dumper streams complets |
| `MCP_URL` | string | `http://127.0.0.1:8000` | URL serveur MCP (appels internes) |

### 🐙 Git & GitHub

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `GITHUB_TOKEN` | secret | — | Personal Access Token (scope: repo, workflow) |

### 📺 YouTube

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `YOUTUBE_API_KEY` | secret | — | YouTube Data API v3 Key (gratuit, 10k unités/jour) |

**Comment obtenir** :
1. Aller sur [Google Cloud Console](https://console.developers.google.com/)
2. Créer un projet (ou sélectionner existant)
3. Activer **YouTube Data API v3**
4. Créer des identifiants → Clé API
5. (Optionnel) Restreindre la clé à YouTube Data API v3

**Quota** :
- Gratuit : 10,000 unités/jour
- Recherche : 100 unités (~100 recherches/jour)
- Détails vidéo : 1 unité (~10,000 requêtes/jour)
- Reset : minuit Pacific Time

### 📧 IMAP Email

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `IMAP_GMAIL_EMAIL` | string | — | Adresse Gmail |
| `IMAP_GMAIL_PASSWORD` | secret | — | App Password Gmail |
| `IMAP_OUTLOOK_EMAIL` | string | — | Adresse Outlook |
| `IMAP_OUTLOOK_PASSWORD` | secret | — | Mot de passe Outlook |
| `IMAP_YAHOO_EMAIL` | string | — | Adresse Yahoo |
| `IMAP_YAHOO_PASSWORD` | secret | — | App Password Yahoo |
| `IMAP_ICLOUD_EMAIL` | string | — | Adresse iCloud |
| `IMAP_ICLOUD_PASSWORD` | secret | — | App Password iCloud |
| `IMAP_INFOMANIAK_EMAIL` | string | — | Adresse Infomaniak |
| `IMAP_INFOMANIAK_PASSWORD` | secret | — | Mot de passe Infomaniak |
| `IMAP_CUSTOM_EMAIL` | string | — | Adresse serveur custom |
| `IMAP_CUSTOM_PASSWORD` | secret | — | Mot de passe custom |
| `IMAP_CUSTOM_SERVER` | string | — | Serveur IMAP (ex: imap.example.com) |
| `IMAP_CUSTOM_PORT` | integer | `993` | Port IMAP |
| `IMAP_CUSTOM_USE_SSL` | boolean | `1` | Utiliser SSL |

### 🚲 Vélib' (Transport)

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `VELIB_STATION_INFO_URL` | string | (Open Data) | URL API stations info |
| `VELIB_STATION_STATUS_URL` | string | (Open Data) | URL API stations status |

### 🔢 Safe JSON

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `BIGINT_AS_STRING` | boolean | `1` | Convertir grands entiers en strings |
| `BIGINT_STR_THRESHOLD` | integer | `50` | Seuil (nombre de chiffres) |
| `PY_INT_MAX_STR_DIGITS` | integer | `10000` | Limite Python int→str |

### 📚 Academic Research

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `ACADEMIC_RS_MAX_ITEMS` | integer | `50` | Nombre max d'articles retournés |
| `ACADEMIC_RS_MAX_ABSTRACT_CHARS` | integer | `2000` | Longueur max des abstracts |
| `ACADEMIC_RS_MAX_BYTES` | integer | `200000` | Taille max du payload JSON |

### 🐍 Script Executor

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `SCRIPT_TIMEOUT_SEC` | integer | `60` | Timeout d'exécution des scripts |

---

## 🔒 Sécurité

### Détection automatique des secrets

Variables contenant ces patterns sont masquées automatiquement :
- `TOKEN`, `PASSWORD`, `KEY`, `SECRET`, `API`, `PASS`, `PWD`

Dans `/control` :
- Type="password" (masqué)
- Valeur masquée : `••••••••` (OWASP compliant)
- Jamais en clair dans les logs

### Protection Git

Le `.env` est **ignoré par Git** (`.gitignore`) :
- ✅ `.env` local jamais commit
- ✅ `.env.example` versionné (sans secrets)
- ✅ Collaborateurs copient et remplissent localement

---

## 📝 Ajouter une variable

1. **Ajouter dans `.env.example`** avec commentaire
2. **Documenter ici** (tableau + hot-reload)
3. **Lire dans le code** :
   ```python
   # ❌ Figé au démarrage
   MY_VAR = os.getenv('MY_VAR', 'default')
   
   # ✅ Hot-reload
   def my_function():
       my_var = os.getenv('MY_VAR', 'default')  # Lit à chaque appel
       return my_var
   ```

---

## 🆘 Troubleshooting

### Variable non prise en compte ?
- Vérifier présence dans `.env`
- Consulter tableau hot-reload ci-dessus
- Si restart nécessaire : `./scripts/dev.sh`

### `.env` synchronisé sur git par erreur ?
```bash
git rm --cached .env
git commit -m "chore: remove .env from git"
# Vérifier que .env est dans .gitignore
```

### Panneau `/control` vide ?
```bash
cp .env.example .env
nano .env  # Remplir les valeurs
```

### YouTube API key invalide ?
- Vérifier que YouTube Data API v3 est **activée** dans Google Cloud Console
- Vérifier que la clé n'a pas de restrictions trop strictes
- Tester avec `curl` :
```bash
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key=YOUR_KEY"
```

---

**Contributions bienvenues !** — Documente tes nouvelles variables ici 🚀
