<div align="center">

<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. 29 tools prêts à l'emploi, orchestrateur LLM avancé, panneau de contrôle web moderne.

[![License: MIT](./LICENSE)](./LICENSE)
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

## 🧰 Outils inclus (29)

Les outils sont groupés par 10 catégories canoniques (invariantes). L'UI affiche "Social & Entertainment" pour la clé `entertainment`.

### 📊 Intelligence & Orchestration
- call_llm — Orchestrateur LLM 2 phases avec streaming
- academic_research_super — Recherche académique multi-sources
- ollama_local — Interface Ollama local + recherche web

### 🔧 Développement
- git — GitHub API + Git local
- gitbook — GitBook discovery/search
- script_executor — Sandbox Python sécurisé

### 📧 Communication
- email_send — Envoi SMTP (Gmail/Infomaniak)
- imap — Réception emails multi-comptes
- discord_webhook — Publication Discord

### 🗄️ Data & Storage
- sqlite_db — SQLite avec chroot
- excel_to_sqlite — Import Excel (.xlsx) → SQLite

### 📄 Documents
- office_to_pdf — Conversion Office → PDF
- pdf_download — Téléchargement PDF
- pdf_search — Recherche PDF
- pdf2text — PDF → texte
- universal_doc_scraper — Scraping documentation

### 🎬 Media
- youtube_search — Recherche YouTube API v3
- youtube_download — Téléchargement YouTube
- video_transcribe — Transcription Whisper
- ffmpeg_frames — Extraction de frames vidéo
- generate_edit_image — Génération/édition d’images (Gemini)

### ✈️ Transportation
- ship_tracker — Navires temps réel (AIS)
- flight_tracker — Avions temps réel
- aviation_weather — Météo en altitude
- velib — Vélos Paris temps réel

### 🌐 Networking
- http_client — Client HTTP/REST universel

### 🔢 Utilities
- math — Calcul avancé (numérique/symbolique/stats)
- date — Utilitaires date/heure

### 🎮 Social & Entertainment
- chess_com — Chess.com API
- reddit_intelligence — Reddit scraping/analysis

> Détails complets : [src/tools/README.md](./src/tools/README.md)

---

## ⚙️ Configuration

### Via le panneau web (recommandé)
http://127.0.0.1:8000/control → 🔐 Configuration

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

# Chess.com (optionnel)
CHESS_COM_RATE_LIMIT_DELAY=0.1
```

Toutes les variables : `.env.example`

---

## 🎨 Panneau de contrôle (UX pro)

http://127.0.0.1:8000/control

- ✅ Groupement clair par catégories avec compte et emoji (catégories fermées par défaut)
- ✅ Badges: nom technique du tool, catégorie visible dans l’en-tête
- ✅ Favoris (★/☆) avec persistance locale
- ✅ Raccourcis clavier: `/` (focus recherche), `Ctrl/Cmd+Enter` (exécuter)
- ✅ Reprise du dernier outil sélectionné
- ✅ Configuration live (hot‑reload) avec secrets masqués

---

## 📚 Documentation

- Guide développeurs LLM : [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)
- Catalog tools : [src/tools/README.md](./src/tools/README.md)
- Changelog : [CHANGELOG.md](./CHANGELOG.md)
- API détails : [src/README.md](./src/README.md)

---

## 📄 Licence

MIT — voir [LICENSE](./LICENSE)
