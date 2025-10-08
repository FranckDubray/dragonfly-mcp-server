# 🔑 Variables d'environnement — Dragonfly MCP Server

Guide complet des variables d'environnement supportées par le serveur.

---

## 🚀 Quick Start

1. **Copier le template** :
   ```bash
   cp .env.example .env
   ```

2. **Remplir les valeurs** (tokens, passwords, etc.)

3. **Démarrer le serveur** :
   ```bash
   ./scripts/dev.sh
   ```

4. **Modifier en live** via le panneau de contrôle :  
   http://127.0.0.1:8000/control → 🔑 Configuration

---

## 🔥 Hot-Reload (sans redémarrage)

### ✅ Variables hot-reload (effet immédiat)

Ces variables sont lues dynamiquement à chaque utilisation :
- **LLM** : `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`, `LLM_REQUEST_TIMEOUT_SEC`
- **Git** : `GITHUB_TOKEN`
- **IMAP** : tous les `IMAP_*_EMAIL`, `IMAP_*_PASSWORD`
- **Vélib'** : `VELIB_STATION_INFO_URL`, `VELIB_STATION_STATUS_URL`
- **Academic** : `ACADEMIC_RS_MAX_ITEMS`, `ACADEMIC_RS_MAX_ABSTRACT_CHARS`, `ACADEMIC_RS_MAX_BYTES`
- **Script** : `SCRIPT_TIMEOUT_SEC`
- **JSON** : `BIGINT_AS_STRING`, `BIGINT_STR_THRESHOLD`

**Comment ?** Modifie via `/control` → Save → effet immédiat dans les prochains appels aux tools.

### ⚠️ Variables nécessitant un restart

Ces variables sont lues au démarrage de l'app et restent figées :
- **Serveur** : `MCP_HOST`, `MCP_PORT`
- **Runtime** : `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`
- **Reload** : `AUTO_RELOAD_TOOLS`, `RELOAD`

**Pourquoi ?** Elles configurent le serveur FastAPI lui-même (bind port, logger, etc.).  
**Solution** : Restart le serveur (`./scripts/dev.sh`) pour appliquer.

---

## 📚 Catégories de variables

### 🌐 Serveur (Network & Runtime)

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `MCP_HOST` | string | `127.0.0.1` | Adresse d'écoute du serveur | ❌ Restart |
| `MCP_PORT` | integer | `8000` | Port d'écoute du serveur | ❌ Restart |
| `LOG_LEVEL` | string | `INFO` | Niveau de log (DEBUG, INFO, WARNING, ERROR) | ❌ Restart |
| `EXECUTE_TIMEOUT_SEC` | integer | `300` | Timeout d'exécution des tools (secondes) | ❌ Restart |
| `AUTO_RELOAD_TOOLS` | boolean | `1` | Détection automatique des nouveaux tools | ❌ Restart |
| `RELOAD` | boolean | `0` | Hot-reload legacy (déprécié) | ❌ Restart |

### 🤖 LLM Orchestration

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `AI_PORTAL_TOKEN` | secret | — | Token d'authentification AI Portal | ✅ Immédiat |
| `LLM_ENDPOINT` | string | — | URL endpoint LLM custom | ✅ Immédiat |
| `LLM_REQUEST_TIMEOUT_SEC` | integer | `300` | Timeout requêtes LLM | ✅ Immédiat |
| `LLM_RETURN_DEBUG` | boolean | `0` | Inclure debug dans les réponses | ✅ Immédiat |
| `LLM_STREAM_TRACE` | boolean | `0` | Tracer les événements SSE | ✅ Immédiat |
| `LLM_STREAM_DUMP` | boolean | `0` | Dumper les streams complets | ✅ Immédiat |
| `MCP_URL` | string | `http://127.0.0.1:8000` | URL du serveur MCP (pour call_llm) | ✅ Immédiat |

### 🐙 Git & GitHub

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `GITHUB_TOKEN` | secret | — | Personal Access Token GitHub (scope: repo, workflow) | ✅ Immédiat |

### 📧 IMAP Email (Multi-comptes)

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `IMAP_GMAIL_EMAIL` | string | — | Adresse Gmail | ✅ Immédiat |
| `IMAP_GMAIL_PASSWORD` | secret | — | App Password Gmail | ✅ Immédiat |
| `IMAP_OUTLOOK_EMAIL` | string | — | Adresse Outlook | ✅ Immédiat |
| `IMAP_OUTLOOK_PASSWORD` | secret | — | Mot de passe Outlook | ✅ Immédiat |
| `IMAP_YAHOO_EMAIL` | string | — | Adresse Yahoo | ✅ Immédiat |
| `IMAP_YAHOO_PASSWORD` | secret | — | App Password Yahoo | ✅ Immédiat |
| `IMAP_ICLOUD_EMAIL` | string | — | Adresse iCloud | ✅ Immédiat |
| `IMAP_ICLOUD_PASSWORD` | secret | — | App Password iCloud | ✅ Immédiat |
| `IMAP_INFOMANIAK_EMAIL` | string | — | Adresse Infomaniak | ✅ Immédiat |
| `IMAP_INFOMANIAK_PASSWORD` | secret | — | Mot de passe Infomaniak | ✅ Immédiat |
| `IMAP_CUSTOM_EMAIL` | string | — | Adresse serveur custom | ✅ Immédiat |
| `IMAP_CUSTOM_PASSWORD` | secret | — | Mot de passe custom | ✅ Immédiat |
| `IMAP_CUSTOM_SERVER` | string | — | Serveur IMAP custom (ex: imap.example.com) | ✅ Immédiat |
| `IMAP_CUSTOM_PORT` | integer | `993` | Port IMAP custom | ✅ Immédiat |
| `IMAP_CUSTOM_USE_SSL` | boolean | `1` | Utiliser SSL pour custom | ✅ Immédiat |

### 🚲 Vélib' (Transport Paris)

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `VELIB_STATION_INFO_URL` | string | (Open Data) | URL API stations info | ✅ Immédiat |
| `VELIB_STATION_STATUS_URL` | string | (Open Data) | URL API stations status | ✅ Immédiat |

### 🔢 Safe JSON (Sérialisation)

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `BIGINT_AS_STRING` | boolean | `1` | Convertir grands entiers en strings | ✅ Immédiat |
| `BIGINT_STR_THRESHOLD` | integer | `50` | Seuil (nombre de chiffres) | ✅ Immédiat |
| `PY_INT_MAX_STR_DIGITS` | integer | `10000` | Limite Python int→str | ✅ Immédiat |

### 📚 Academic Research

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `ACADEMIC_RS_MAX_ITEMS` | integer | `50` | Nombre max d'articles retournés | ✅ Immédiat |
| `ACADEMIC_RS_MAX_ABSTRACT_CHARS` | integer | `2000` | Longueur max des abstracts | ✅ Immédiat |
| `ACADEMIC_RS_MAX_BYTES` | integer | `200000` | Taille max du payload JSON | ✅ Immédiat |

### 🐍 Script Executor

| Variable | Type | Défaut | Description | Hot-reload |
|----------|------|--------|-------------|------------|
| `SCRIPT_TIMEOUT_SEC` | integer | `60` | Timeout d'exécution des scripts | ✅ Immédiat |

---

## 🔒 Sécurité

### Variables sensibles (secrets)

Les variables contenant ces patterns sont automatiquement détectées comme secrets :
- `TOKEN`
- `PASSWORD`
- `KEY`
- `SECRET`
- `API`
- `PASS`
- `PWD`

**Dans le panneau /control** :
- Input type="password" (masqué)
- Valeur actuelle masquée : `****xxxx`
- Jamais exposées en clair dans les logs

### Protection Git

Le `.env` est **ignoré par Git** (`.gitignore`) :
- ✅ Ton `.env` local n'est jamais commit
- ✅ Le `.env.example` est versionné (sans secrets)
- ✅ Collaborateurs copient `.env.example` → `.env` et remplissent leurs valeurs

---

## 📝 Ajouter une nouvelle variable

1. **Ajouter dans `.env.example`** (avec commentaire)
2. **Documenter ici** (tableau + hot-reload status)
3. **La lire dans ton code** :
   ```python
   import os
   MY_VAR = os.getenv('MY_NEW_VAR', 'default_value')
   ```
4. **Si hot-reload souhaité** : lire via `os.getenv()` à chaque utilisation (pas au top-level)

### Exemple : variable hot-reload

```python
# ❌ FIGÉ au démarrage
MY_VAR = os.getenv('MY_VAR', 'default')

def my_function():
    return MY_VAR  # Ancienne valeur, même après modif via /control
```

```python
# ✅ HOT-RELOAD
def my_function():
    my_var = os.getenv('MY_VAR', 'default')  # Lit à chaque appel
    return my_var  # Nouvelle valeur si modifiée via /control
```

---

## 🎯 Workflow typique

1. **Setup initial** :
   ```bash
   cp .env.example .env
   nano .env  # Remplir GITHUB_TOKEN, AI_PORTAL_TOKEN, etc.
   ./scripts/dev.sh
   ```

2. **Modifier en live** :
   - Ouvrir http://127.0.0.1:8000/control
   - Cliquer 🔑 Configuration
   - Modifier une variable (ex: `LLM_REQUEST_TIMEOUT_SEC`)
   - Save → effet immédiat dans les prochains appels

3. **Ajouter un compte IMAP** :
   - Ajouter dans `.env` : `IMAP_GMAIL_EMAIL=...`, `IMAP_GMAIL_PASSWORD=...`
   - Ou via `/control` → remplir les champs → Save
   - Utiliser immédiatement sans restart !

---

## 🆘 Troubleshooting

### Variable non prise en compte ?

- **Vérifier** : elle existe dans le `.env` ?
- **Hot-reload ?** Consulter le tableau ci-dessus
- **Si restart nécessaire** : `./scripts/dev.sh`

### .env synchronisé sur git par erreur ?

```bash
git rm --cached .env
git commit -m "chore: remove .env from git"
```

Puis vérifier que `.env` est dans `.gitignore`.

### Panneau /control vide ?

Le serveur n'a pas de `.env` → créer depuis `.env.example`.

---

**Contributions bienvenues !** — Ajoute tes variables et documente-les ici 🚀
