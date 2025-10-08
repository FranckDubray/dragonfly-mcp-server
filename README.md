<div align="center">

<!-- Local logo for reliability (placed in assets/) -->
<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. Découverte automatique des tools, exécution sécurisée, orchestrateur LLM avancé, et panneau de contrôle web.

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
- Panneau de contrôle web pour configurer et tester (`/control`)

> Pour les détails d'API (endpoints, sérialisation JSON, etc.), consultez aussi [src/README.md](./src/README.md).

---

## 📚 Sommaire
- [Fonctionnalités](#-fonctionnalités)
- [Demo rapide](#-demo-rapide)
- [Installation](#-installation)
- [Outils inclus](#-outils-inclus)
- [Configuration](#-configuration)
- [Sécurité](#-sécurité)
- [Structure du projet](#-structure-du-projet)
- [Pour les LLM « développeurs »](#-pour-les-llm-développeurs)
- [Licence](#-licence)

---

## 🚀 Fonctionnalités
- Auto‑reload des tools (détection de nouveaux fichiers dans `src/tools/`)
- JSON « sûr »: grands entiers, NaN/Infinity sanitisés
- Orchestration LLM streaming en 2 phases (avec cumul d'usage multi‑niveaux)
- Panneau de contrôle web (`/control`)
- **15 tools prêts à l'emploi** couvrant Git, bases de données, PDF, IA, emails, Discord, calcul, etc.

---

## ⚡ Demo rapide

### Exécuter un tool de base
```bash
curl -s -X POST http://127.0.0.1:8000/execute \
 -H 'Content-Type: application/json' \
 -d '{"tool":"date","params":{"operation":"today"}}'
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
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
cd dragonfly-mcp-server
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

**Démarrage:**
- Linux/macOS: `./scripts/dev.sh`
- Windows: `scripts\dev.ps1`

Par défaut: http://127.0.0.1:8000

Panneau de contrôle: http://127.0.0.1:8000/control

---

## 🧪 Outils inclus (15 tools)

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

#### **imap** — Emails multi-comptes ⭐ NOUVEAU
- **6 providers**: Gmail, Outlook, Yahoo, iCloud, Infomaniak, Custom
- **Multi-comptes simultanés** via variables d'env par provider
- **13 opérations**: connect, list_folders, search, get, download, mark read/unread (batch), move (batch), spam, delete (batch)
- **Sécurité**: credentials uniquement en `.env`, jamais en paramètres
- Configuration:
  ```bash
  IMAP_GMAIL_EMAIL=user@gmail.com
  IMAP_GMAIL_PASSWORD=app_password
  IMAP_INFOMANIAK_EMAIL=contact@domain.com
  IMAP_INFOMANIAK_PASSWORD=password
  ```

#### **discord_webhook** — Publication Discord
- CRUD complet avec persistance SQLite
- Publication d'articles (Embeds)
- Split automatique des longs messages
- Gestion des webhooks multiples

---

### 🔧 Développement & Git

#### **git** — Git unifié (GitHub API + local)
- **GitHub API**: create_repo, add/delete files, branches, commits, diff, merge
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

#### **ffmpeg_frames** — Extraction de frames vidéo
- **Détection native PyAV** (frame-by-frame)
- Moving average + hysteresis + NMS + refinement
- Debug per-frame: temps, diff, similarité%
- Haute précision sur vidéos compressées (YouTube)
- Export: images + timestamps + debug.json

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

Variables principales (`.env` ou `/control`):

```bash
# Réseau
MCP_HOST=127.0.0.1
MCP_PORT=8000

# LLM
AI_PORTAL_TOKEN=your_token
LLM_ENDPOINT=https://api.example.com

# IMAP (multi-comptes)
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=app_password
IMAP_INFOMANIAK_EMAIL=contact@domain.com
IMAP_INFOMANIAK_PASSWORD=password

# Git
GITHUB_TOKEN=ghp_xxxxx

# Divers
EXECUTE_TIMEOUT_SEC=300
AUTO_RELOAD_TOOLS=1
```

---

## 🔒 Sécurité

- **SQLite chroot**: DBs sous `<projet>/sqlite3`
- **Git local**: opérations limitées à la racine projet
- **Script executor**: sandbox stricte
- **IMAP**: credentials en `.env` uniquement, jamais en paramètres
- **Safe JSON**: NaN/Infinity/grands entiers sanitisés

---

## 🗂 Structure du projet

```
src/
  app_factory.py     # FastAPI app, endpoints, auto-reload
  server.py          # Entrée Uvicorn
  config.py          # .env (load/save), masquage secrets
  tools/             # 15 tools (run() + spec())
    _call_llm/       # Orchestrateur LLM
    _math/           # Modules calcul
    _ffmpeg/         # FFmpeg utils
    _git/            # Git local + GitHub
    _imap/           # IMAP multi-comptes
    _discord_webhook/# Discord integration
    _script/         # Sandbox ScriptExecutor
    # ... + tools simples (date, pdf, reddit, etc.)
  tool_specs/        # Specs JSON canoniques
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
