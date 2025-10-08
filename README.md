<div align="center">

<!-- Local logo for reliability (placed in assets/) -->
<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. Découverte automatique des tools, exécution sécurisée, orchestrateur LLM avancé, et panneau de contrôle web moderne.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688)
![Status](https://img.shields.io/badge/Status-Active-success)

</div>

---

## ✨ Vue d'ensemble
Dragonfly MCP Server expose des « tools » (au format OpenAI tools) via des endpoints HTTP simples:
- Découverte automatique des outils sous `src/tools/`
- Exécution d'un tool via `POST /execute`
- Orchestration LLM en 2 phases via `call_llm` (avec usage cumulatif)
- **Panneau de contrôle web moderne** pour configurer et tester (`/control`)
- **Configuration automatique** des variables d'environnement

> Pour les détails d'API (endpoints, sérialisation JSON, etc.), consultez aussi [src/README.md](./src/README.md).

---

## 📚 Sommaire
- [Fonctionnalités](#-fonctionnalités)
- [Demo rapide](#-demo-rapide)
- [Installation](#-installation)
- [Outils inclus](#-outils-inclus)
- [Configuration](#-configuration)
- [Panneau de contrôle](#-panneau-de-contrôle)
- [Sécurité](#-sécurité)
- [Structure du projet](#-structure-du-projet)
- [Pour les LLM « développeurs »](#-pour-les-llm-développeurs)
- [Licence](#-licence)

---

## 🚀 Fonctionnalités
- Auto‑reload des tools (détection de nouveaux fichiers dans `src/tools/`)
- JSON « sûr »: grands entiers, NaN/Infinity sanitisés
- Orchestration LLM streaming en 2 phases (avec cumul d'usage multi‑niveaux)
- **Panneau de contrôle web moderne** (design épuré, sidebar, logo HD)
- **Configuration générique** : gestion automatique de toutes les variables d'environnement
- **Hot-reload** : modifiez les variables en live sans restart (via `/control`)
- **20 tools prêts à l'emploi** couvrant Git, bases de données, PDF, IA, emails, Discord, transport, vidéo, YouTube, calcul, etc.

---

## ⚡ Demo rapide

### Exécuter un tool de base
```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{"tool":"date","params":{"operation":"today"}}'
```

### Télécharger et transcrire une vidéo YouTube 🆕
```bash
# 1. Télécharger l'audio d'une vidéo YouTube
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"youtube_download",
   "params":{
     "url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ",
     "media_type":"audio"
   }
 }'

# 2. Transcrire avec Whisper (parallèle 3x, ultra rapide)
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"video_transcribe",
   "params":{
     "operation":"transcribe",
     "path":"docs/video/nom_fichier.mp3"
   }
 }'
```

### Télécharger un PDF depuis arXiv
```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"pdf_download",
   "params":{
     "operation":"download",
     "url":"https://arxiv.org/pdf/2301.00001.pdf",
     "filename":"research_paper"
   }
 }'
```

### Lire les emails non lus (IMAP multi-comptes)
```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"imap",
   "params":{
     "provider":"gmail",
     "operation":"search_messages",
     "folder":"inbox",
     "query":{"unseen":true},
     "max_results":20
   }
 }'
```

### Trouver une station Vélib' disponible
```bash
# 1. Rechercher stations près de Bastille
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"sqlite_db",
   "params":{
     "db_name":"velib",
     "query":"SELECT station_code, name, capacity FROM stations WHERE name LIKE '\''%Bastille%'\'' ORDER BY capacity DESC LIMIT 3"
   }
 }'

# 2. Obtenir disponibilité temps réel
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"velib",
   "params":{
     "operation":"get_availability",
     "station_code":"12001"
   }
 }'
```

### Orchestrer un LLM
```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{
   "tool":"call_llm",
   "params":{"message":"Dis bonjour en français.","model":"gpt-4o"}
 }'
```

---

## 🛠 Installation

**Prérequis:** Python 3.11 ou 3.12

```bash
# 1. Cloner le repo
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
cd dragonfly-mcp-server

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install -U pip
pip install -e ".[dev]"

# 4. Démarrer le serveur (crée automatiquement .env depuis .env.example)
./scripts/dev.sh
```

**Le script `dev.sh` fait automatiquement** :
- ✅ Copie `.env.example` → `.env` si absent
- ✅ Crée le venv si nécessaire
- ✅ Installe toutes les dépendances
- ✅ Démarre le serveur

Par défaut: http://127.0.0.1:8000

---

## 🧪 Outils inclus (20 tools)

### 🤖 Intelligence & Orchestration

#### **call_llm** — Orchestrateur LLM avancé
- 2 phases: tools → texte final
- Usage cumulatif automatique
- Support streaming
- Paramètres: `message`, `model`, `tool_names`, `promptSystem`

#### **academic_research_super** — Recherche académique
- Pipeline complet: agrégation, scraping, synthèse
- Sources multiples (arXiv, PubMed, etc.)
- Export formaté

#### **script_executor** — Exécution de scripts Python
- Sandbox sécurisé
- Orchestration de tools
- Isolation complète

---

### 📧 Communication & Collaboration

#### **imap** — Emails multi-comptes ⭐
- **6 providers**: Gmail, Outlook, Yahoo, iCloud, Infomaniak, Custom
- **Multi-comptes simultanés** via variables d'env par provider
- **13 opérations**: connect, list_folders, search, get, download, mark read/unread (batch), move (batch), spam, delete (batch)
- **Sécurité**: credentials uniquement en `.env`, jamais en paramètres
- Configuration automatique via panneau `/control`

#### **discord_webhook** — Publication Discord
- CRUD complet avec persistance SQLite
- Publication d'articles (Embeds)
- Split automatique des longs messages
- Gestion des webhooks multiples

---

### 🔧 Développement & Git

#### **git** — Git unifié (GitHub API + local)
- **GitHub API**: create_repo, add/delete files, branches, commits, diff, merge, create_release
- **Git local**: status, fetch, pull, rebase, branch_create, checkout, commit, push, log
- **Sécurité**: opérations chroot au projet
- Support des conflits avec hints

#### **gitbook** — GitBook discovery/search
- Discovery automatique de GitBook sites
- Recherche full-text
- Extraction de contenu

---

### 🗄️ Bases de données & Storage

#### **sqlite_db** — SQLite chroot
- Bases sous `<projet>/sqlite3`
- Exécution sécurisée de requêtes
- Support transactions
- Noms de DB validés

---

### 📄 Documents & PDF

#### **pdf_download** — Téléchargement PDF
- **Télécharge des PDFs depuis URLs** vers `docs/pdfs`
- Validation PDF (magic bytes `%PDF-`)
- **Métadonnées automatiques** : pages, titre, auteur
- Noms de fichiers uniques (suffixes `_1`, `_2`, etc.)
- Timeout configurable (5-300s)

#### **pdf_search** — Recherche dans PDF
- Recherche par mots-clés
- Extraction de contexte
- Support multi-pages

#### **pdf2text** — Extraction texte PDF
- Conversion PDF → texte
- Préservation de la structure
- Support batch

#### **universal_doc_scraper** — Scraper web universel
- Extraction intelligente de contenu
- Support multi-formats
- Nettoyage automatique

---

### 🎬 Média & FFmpeg

#### **youtube_download** — Téléchargement YouTube 🆕
- **Télécharge vidéos/audio** depuis YouTube vers `docs/video/`
- **Modes** : audio (MP3, parfait transcription), video (MP4), both (séparés)
- **Qualités** : best, 720p, 480p, 360p
- **Features** :
  - Validation URL YouTube (tous formats supportés)
  - Filename sanitization automatique
  - Unique naming (_1, _2 si fichier existe)
  - Duration check (évite téléchargements massifs)
  - Metadata extraction (titre, durée, uploader, vues)
- **Workflow intégré** : YouTube → Audio → video_transcribe → Texte exploitable
- **Opérations** : download, get_info

#### **video_transcribe** — Transcription vidéo Whisper
- **Extraction audio** : FFmpeg extraction directe par segment
- **Transcription Whisper** : API multipart avec Bearer token
- **Parallélisation** : traitement par batch de 3 chunks simultanés (3x plus rapide)
- **Segmentation** : `time_start`/`time_end` pour grosses vidéos
- **Performance** : 3 minutes de vidéo → 20 secondes de traitement
- **Retour JSON** : segments avec timestamps + texte complet
- **Opérations** : transcribe, get_info

#### **ffmpeg_frames** — Extraction de frames vidéo
- **Détection native PyAV** (frame-by-frame)
- Moving average + hysteresis + NMS + refinement
- Debug per-frame: temps, diff, similarité%
- Haute précision sur vidéos compressées (YouTube)
- Export: images + timestamps + debug.json

---

### 🚲 Transport & Mobilité

#### **velib** — Vélib' Métropole Paris
- **Gestionnaire de cache** des stations Vélib' (~1494 stations)
- **3 opérations**: refresh_stations, get_availability, check_cache
- **Cache SQLite** : station_code, name, lat, lon, capacity
- **Temps réel** : vélos mécaniques/électriques, places libres
- **Recherches** via `sqlite_db` (db_name: 'velib')
- **API Open Data** : pas d'authentification requise

---

### 🌐 Networking & API

#### **http_client** — Client HTTP universel
- **Tous les verbes HTTP** : GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Authentification** : Basic, Bearer, API Key
- **Body formats** : JSON, Form data, Raw text/XML
- **Features avancées** : Retry avec backoff, Proxy, Timeout, SSL verification
- **Response parsing** : auto-detect, JSON, text, raw
- **Sauvegarde optionnelle** des réponses

---

### 🔢 Calcul & Math

#### **math** — Calcul avancé
- **Numérique**: arithmétique, trig, log, exp, sqrt
- **High-precision**: mpmath pour grandes précisions
- **Symbolique**: dérivées, intégrales, simplification (sympy)
- **Algèbre linéaire**: matrices, vecteurs, eigenvalues, SVD, LU, QR
- **Probabilités**: stats, distributions (normale, Poisson, binomiale, etc.)
- **Polynômes**: racines, factorisation
- **Solveurs**: équations, systèmes, optimisation
- **Nombres premiers**: nth_prime, factorisation, Euler phi
- **Séries**: sommes finies/infinies, produits

#### **date** — Manipulation de dates
- Opérations: now, today, diff, add, format, parse, weekday, week_number
- Timezone aware
- Formats multiples

---

### 🌐 Social Media

#### **reddit_intelligence** — Reddit scraping/analysis
- Extraction de posts/comments
- Analyse de sentiment
- Trending topics

---

## ⚙️ Configuration

### 🎯 Configuration automatique (recommandé)

**Au premier démarrage** :
```bash
./scripts/dev.sh
```

Le script crée automatiquement `.env` depuis `.env.example`.

**Modifier les variables** :
1. Ouvrir http://127.0.0.1:8000/control
2. Cliquer **🔑 Configuration**
3. Toutes les variables s'affichent automatiquement
4. Modifier les valeurs → **Save**
5. **Hot-reload** : effet immédiat pour 90% des variables !

### 📝 Configuration manuelle (optionnel)

```bash
# Éditer directement le .env
nano .env
```

Variables principales (32 variables disponibles) :

```bash
# Réseau
MCP_HOST=127.0.0.1
MCP_PORT=8000

# LLM
AI_PORTAL_TOKEN=your_token
LLM_ENDPOINT=https://ai.dragonflygroup.fr

# IMAP (multi-comptes)
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=app_password
IMAP_INFOMANIAK_EMAIL=contact@domain.com
IMAP_INFOMANIAK_PASSWORD=password

# Git
GITHUB_TOKEN=ghp_xxxxx

# Voir .env.example pour la liste complète (32 variables)
```

**Documentation complète** : [ENV_VARIABLES.md](./ENV_VARIABLES.md)

---

## 🎨 Panneau de contrôle

### Interface moderne (v1.7.0)

Accès : **http://127.0.0.1:8000/control**

**Design** :
- ✅ Layout 2 colonnes (Sidebar + Zone de travail)
- ✅ Logo HD Dragonfly professionnel
- ✅ Un seul tool visible à la fois (fini le scroll d'enfer)
- ✅ Search bar pour filtrer les 20 tools
- ✅ Fond blanc propre, design épuré
- ✅ Responsive mobile-ready

**Features** :
- 🔧 **Tools** : formulaire complet pour chaque tool avec paramètres
- 🔑 **Configuration** : modification des variables d'environnement
  - Génération automatique de tous les champs depuis `.env`
  - Détection automatique des secrets (masquage total `••••••••`)
  - Hot-reload : 90% des variables sans restart
  - Badges colorés (present/absent)
- 🔍 **Recherche** : filtre instantané des tools
- ⚡ **Exécution** : test direct des tools avec affichage des résultats

---

## 🔒 Sécurité

- **SQLite chroot**: DBs sous `<projet>/sqlite3`
- **Git local**: opérations limitées à la racine projet
- **Script executor**: sandbox stricte
- **IMAP**: credentials en `.env` uniquement, jamais en paramètres
- **PDF download**: validation magic bytes, chroot `docs/pdfs`
- **YouTube download**: validation URL YouTube, chroot `docs/video/`, duration limits
- **Vélib'**: API publique (pas de secrets), chroot SQLite
- **HTTP Client**: timeout, SSL verification, credentials masqués
- **Video transcribe**: chroot `docs/video/`, cleanup temp files
- **Safe JSON**: NaN/Infinity/grands entiers sanitisés
- **Secrets masqués totalement** : zéro caractère exposé (OWASP compliant)
- **.env ignoré par git** : aucun risque de commit de secrets

---

## 🗂 Structure du projet

```
src/
  app_factory.py     # FastAPI app, endpoints, auto-reload
  server.py          # Entrée Uvicorn
  config.py          # .env (load/save), masquage secrets
  ui_html.py         # Panneau de contrôle HTML
  ui_js.py           # Panneau de contrôle JavaScript
  tools/             # 20 tools (run() + spec())
    _call_llm/       # Orchestrateur LLM
    _math/           # Modules calcul
    _ffmpeg/         # FFmpeg utils
    _git/            # Git local + GitHub
    _imap/           # IMAP multi-comptes
    _pdf_download/   # PDF download
    _http_client/    # HTTP client universel
    _discord_webhook/# Discord integration
    _script/         # Sandbox ScriptExecutor
    _velib/          # Vélib' cache manager
    _video_transcribe/ # Video transcription Whisper
    _youtube_download/ # YouTube downloader 🆕
    # ... + tools simples (date, pdf, reddit, etc.)
  tool_specs/        # Specs JSON canoniques
scripts/
  dev.sh             # Script de démarrage (Linux/macOS)
  dev.ps1            # Script de démarrage (Windows)
.env.example         # Template de configuration (32 variables)
ENV_VARIABLES.md     # Documentation des variables
```

---

## 👩‍💻 Pour les LLM « développeurs »

Guide complet: [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)

- Conventions, invariants, checklists
- Règles spec JSON (parameters = object, arrays → items)
- Détails `call_llm` (streaming, usage cumulatif)
- Safe JSON

---

## 📄 Licence

MIT — voir [LICENSE](./LICENSE)

---

**Contributions bienvenues** — Issues & PRs sur [GitHub](https://github.com/FranckDubray/dragonfly-mcp-server) !
