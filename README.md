<div align="center">

<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. 25 tools prêts à l'emploi, orchestrateur LLM avancé, panneau de contrôle web moderne.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688)

</div>

---

## 🚀 Installation

```bash
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
cd dragonfly-mcp-server
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -U pip && pip install -e ".[dev]"
./scripts/dev.sh
```

Par défaut: http://127.0.0.1:8000

---

## 🧪 Outils inclus (25)

### 🤖 Intelligence & Orchestration
- **call_llm** — Orchestrateur LLM 2 phases avec streaming
- **academic_research_super** — Recherche académique multi-sources
- **script_executor** — Sandbox Python sécurisé

### 📧 Communication
- **email_send** 🆕 — Envoi SMTP (Gmail/Infomaniak)
- **imap** — Réception emails multi-comptes
- **discord_webhook** — Publication Discord

### 🔧 Développement
- **git** — GitHub API + Git local
- **gitbook** — GitBook discovery/search

### 🗄️ Bases de données
- **sqlite_db** — SQLite avec chroot

### 📄 Documents
- **pdf_download** — Téléchargement PDF depuis URLs
- **pdf_search** — Recherche dans PDFs
- **pdf2text** — Extraction texte PDF
- **universal_doc_scraper** — Scraping web

### 🎬 Média
- **youtube_search** 🆕 — Recherche YouTube API v3
- **youtube_download** — Téléchargement YouTube
- **video_transcribe** 🆕 — Transcription Whisper avec timing
- **ffmpeg_frames** — Extraction frames vidéo

### ✈️ Transport
- **ship_tracker** — Suivi navires temps réel (AIS)
- **flight_tracker** — Suivi avions temps réel
- **aviation_weather** — Météo aviation altitude
- **velib** — Vélib' Paris temps réel

### 🌐 Networking
- **http_client** — Client HTTP/REST universel

### 🔢 Calcul
- **math** — Calcul avancé (numérique, symbolique, stats)
- **date** — Manipulation dates

### 🌐 Social
- **reddit_intelligence** — Reddit scraping/analysis

> Détails complets : [src/tools/README.md](./src/tools/README.md)

---

## ⚙️ Configuration

### Via le panneau web (recommandé)
http://127.0.0.1:8000/control → **🔑 Configuration**

### Variables principales
```bash
# LLM
AI_PORTAL_TOKEN=your_token
LLM_ENDPOINT=https://ai.dragonflygroup.fr

# Emails (Gmail/Infomaniak) - partagées imap + email_send
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=app_password
IMAP_INFOMANIAK_EMAIL=contact@domain.com
IMAP_INFOMANIAK_PASSWORD=password

# YouTube
YOUTUBE_API_KEY=your_key

# Ship tracking
AISSTREAM_API_KEY=your_key

# Git
GITHUB_TOKEN=ghp_xxxxx
```

Toutes les variables : `.env.example`

---

## 🎨 Panneau de contrôle

http://127.0.0.1:8000/control

- ✅ Test des 25 tools
- ✅ Configuration live (hot-reload)
- ✅ Search bar
- ✅ Secrets masqués

---

## 📚 Documentation

- **Guide développeurs LLM** : [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)
- **Catalog tools** : [src/tools/README.md](./src/tools/README.md)
- **Changelog** : [CHANGELOG.md](./CHANGELOG.md)
- **API détails** : [src/README.md](./src/README.md)

---

## 📄 Licence

MIT — voir [LICENSE](./LICENSE)
