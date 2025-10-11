# 🧰 Dragonfly Tools Catalog

Catalog complet des 34 tools disponibles, organisés par catégorie canonique.

---

## 📊 Intelligence & Orchestration (3)

### call_llm
Orchestrateur LLM avancé à 2 phases avec streaming.
- **Opérations**: 2-phase reasoning, streaming
- **Token**: AI_PORTAL_TOKEN
- **Catégorie**: intelligence

### academic_research_super
Recherche académique multi-sources (arXiv, PubMed, Semantic Scholar).
- **Opérations**: search, get_paper, get_citations
- **Token**: aucun (gratuit)
- **Catégorie**: intelligence
- **Tags**: knowledge, research, external_sources

### ollama_local
Interface Ollama local + recherche web intégrée.
- **Opérations**: chat, generate, list_models, web_search
- **Token**: aucun (local)
- **Catégorie**: intelligence

---

## 🔧 Development (3)

### git
GitHub API + Git local complet.
- **Opérations**: 20+ ops (repos, branches, commits, releases, diff, merge...)
- **Token**: GITHUB_TOKEN
- **Catégorie**: development

### gitbook
GitBook discovery et recherche de documentation.
- **Opérations**: search_gitbook, discover_gitbook
- **Token**: aucun
- **Catégorie**: development
- **Tags**: knowledge, docs, search

### script_executor
Sandbox Python sécurisé pour exécution de code.
- **Opérations**: execute
- **Token**: aucun
- **Catégorie**: development

---

## 📧 Communication (4)

### email_send
Envoi emails via SMTP (Gmail, Infomaniak).
- **Opérations**: send_email
- **Token**: IMAP_GMAIL_EMAIL + PASSWORD ou IMAP_INFOMANIAK_EMAIL + PASSWORD
- **Catégorie**: communication

### imap
Réception emails multi-comptes (Gmail, Infomaniak).
- **Opérations**: list_accounts, select_account, list_folders, search_emails, get_email, delete_email
- **Token**: IMAP_GMAIL_EMAIL + PASSWORD ou IMAP_INFOMANIAK_EMAIL + PASSWORD
- **Catégorie**: communication

### discord_webhook
Publication messages Discord via webhooks.
- **Opérations**: send (text/embed)
- **Token**: webhook URL
- **Catégorie**: communication

### telegram_bot 🆕
Bot Telegram complet (messages, médias, polls).
- **Opérations**: send_message, send_photo, send_document, send_location, send_video, get_updates, get_me, delete_message, edit_message, send_poll
- **Token**: TELEGRAM_BOT_TOKEN
- **Catégorie**: communication
- **Gratuit**: illimité

---

## 🗄️ Data & Storage (3)

### sqlite_db
Gestion SQLite avec chroot sécurisé.
- **Opérations**: execute, query, schema, list_tables, create_table, insert, update, delete, backup
- **Token**: aucun
- **Catégorie**: data

### excel_to_sqlite
Import Excel (.xlsx) → SQLite.
- **Opérations**: import
- **Token**: aucun
- **Catégorie**: data

### coingecko 🆕
Données crypto complètes (prix, market, trending).
- **Opérations**: get_price, get_coin_info, search_coins, get_market_chart, get_trending, get_global_data, list_coins, get_exchanges, get_coin_history, compare_coins
- **Token**: aucun (gratuit 50 calls/min)
- **Catégorie**: data
- **Tags**: crypto, cryptocurrency, prices, market_data

---

## 📄 Documents (5)

### office_to_pdf
Conversion Office → PDF (LibreOffice).
- **Opérations**: convert
- **Token**: aucun
- **Catégorie**: documents

### pdf_download
Téléchargement PDF depuis URL.
- **Opérations**: download
- **Token**: aucun
- **Catégorie**: documents

### pdf_search
Recherche dans fichiers PDF.
- **Opérations**: search
- **Token**: aucun
- **Catégorie**: documents

### pdf2text
Extraction texte depuis PDF.
- **Opérations**: extract
- **Token**: aucun
- **Catégorie**: documents

### universal_doc_scraper
Scraping documentation technique (MkDocs, GitBook, Sphinx...).
- **Opérations**: scrape
- **Token**: aucun
- **Catégorie**: documents
- **Tags**: scraping, docs

---

## 🎬 Media (5)

### youtube_search
Recherche YouTube API v3.
- **Opérations**: search_videos, get_video_details, get_channel_info, get_playlist_items
- **Token**: YOUTUBE_API_KEY ou GOOGLE_API_KEY (fallback)
- **Catégorie**: media

### youtube_download
Téléchargement vidéos YouTube (yt-dlp).
- **Opérations**: download
- **Token**: aucun
- **Catégorie**: media

### video_transcribe
Transcription audio/vidéo (Whisper).
- **Opérations**: transcribe
- **Token**: aucun (local)
- **Catégorie**: media

### ffmpeg_frames
Extraction frames vidéo (FFmpeg).
- **Opérations**: extract_frames
- **Token**: aucun
- **Catégorie**: media

### generate_edit_image
Génération/édition images (Gemini).
- **Opérations**: generate, edit
- **Token**: AI_PORTAL_TOKEN
- **Catégorie**: media

---

## ✈️ Transportation (4)

### ship_tracker
Suivi navires temps réel (AIS).
- **Opérations**: track_ship, search_ships
- **Token**: AISSTREAM_API_KEY
- **Catégorie**: transportation

### flight_tracker
Suivi avions temps réel (AviationStack).
- **Opérations**: track_flight, search_flights, get_airport, get_airline
- **Token**: AVIATIONSTACK_API_KEY
- **Catégorie**: transportation

### aviation_weather
Météo aviation (METAR/TAF).
- **Opérations**: get_metar, get_taf
- **Token**: aucun (NOAA gratuit)
- **Catégorie**: transportation

### velib
Disponibilité vélos Vélib' Paris temps réel.
- **Opérations**: search_stations, get_station
- **Token**: aucun (API publique)
- **Catégorie**: transportation

---

## 🌐 Networking (1)

### http_client
Client HTTP/REST universel.
- **Opérations**: request (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- **Token**: aucun
- **Catégorie**: networking

---

## 🔢 Utilities (5)

### math
Calcul avancé (numérique/symbolique/stats).
- **Opérations**: calculate, solve_equation, differentiate, integrate, plot, matrix_operations, statistics, prime_factors, gcd_lcm
- **Token**: aucun
- **Catégorie**: utilities

### date
Utilitaires date/heure.
- **Opérations**: now, parse, format, add, subtract, diff, timezone_convert
- **Token**: aucun
- **Catégorie**: utilities

### device_location
Localisation device par IP (géolocalisation).
- **Opérations**: get_location
- **Token**: aucun (gratuit)
- **Catégorie**: utilities

### openweathermap 🆕
Météo complète (actuelle, prévisions, qualité air).
- **Opérations**: current_weather, forecast_5day, forecast_hourly, air_pollution, geocoding, reverse_geocoding, weather_alerts, onecall
- **Token**: OPENWEATHERMAP_API_KEY
- **Gratuit**: 60 calls/min
- **Catégorie**: utilities
- **Tags**: weather, forecast, air_quality, geocoding

### google_maps 🆕
Google Maps complet (geocoding, directions, places).
- **Opérations**: geocode, reverse_geocode, directions, distance_matrix, places_search, place_details, places_nearby, timezone, elevation
- **Token**: GOOGLE_MAPS_API_KEY ou GOOGLE_API_KEY (fallback)
- **Gratuit**: $200 crédit/mois (~28k geocoding)
- **Catégorie**: utilities
- **Tags**: maps, geocoding, directions, places, navigation

---

## 🎮 Social & Entertainment (2)

### chess_com
Chess.com API (joueurs, parties, puzzles...).
- **Opérations**: 24 ops (player_profile, player_stats, player_games, titled_players, leaderboards...)
- **Token**: aucun (API publique)
- **Catégorie**: entertainment

### reddit_intelligence
Reddit scraping et analyse.
- **Opérations**: search_posts, get_subreddit_info, get_post_comments, analyze_sentiment
- **Token**: aucun
- **Catégorie**: entertainment
- **Tags**: social, knowledge, scraping, external_sources

---

## 📊 Statistiques

- **Total tools**: 34
- **Gratuits (pas de token)**: 18
- **Tokens requis**: 16
- **Nouveaux (v1.15.0)**: 4 (openweathermap, coingecko, google_maps, telegram_bot)

---

## 🔑 Tokens requis (récapitulatif)

| Token | Tools | Gratuit ? |
|-------|-------|-----------|
| AI_PORTAL_TOKEN | call_llm, generate_edit_image | Payant |
| GITHUB_TOKEN | git | Gratuit |
| IMAP_GMAIL_EMAIL + PASSWORD | imap, email_send | Gratuit |
| IMAP_INFOMANIAK_EMAIL + PASSWORD | imap, email_send | Gratuit |
| TELEGRAM_BOT_TOKEN | telegram_bot | Gratuit ✅ |
| YOUTUBE_API_KEY (ou GOOGLE_API_KEY) | youtube_search | Gratuit ✅ |
| GOOGLE_MAPS_API_KEY (ou GOOGLE_API_KEY) | google_maps | $200 crédit/mois ✅ |
| OPENWEATHERMAP_API_KEY | openweathermap | Gratuit ✅ |
| AISSTREAM_API_KEY | ship_tracker | Gratuit |
| AVIATIONSTACK_API_KEY | flight_tracker | Freemium |

---

## 🆕 Dernières additions

### v1.15.0 (11/01/2025)
- **openweathermap** (utilities) — Météo complète
- **coingecko** (data) — Crypto données
- **google_maps** (utilities) — Maps complet
- **telegram_bot** (communication) — Bot Telegram

### v1.14.3 (11/10/2025)
- **device_location** (utilities) — Localisation IP

### v1.14.0 (11/01/2025)
- **chess_com** (entertainment) — Chess.com API

---

## 📖 Documentation complète

Chaque tool possède :
- Spec JSON canonique : `src/tool_specs/<tool_name>.json`
- Bootstrap Python : `src/tools/<tool_name>.py`
- Package implémentation : `src/tools/_<tool_name>/`
  - `api.py` — Routing
  - `core.py` — Logique métier
  - `validators.py` — Validation
  - `utils.py` — Helpers
  - `services/` — I/O (HTTP, DB, files)

Voir [LLM_DEV_GUIDE.md](../../LLM_DEV_GUIDE.md) pour créer de nouveaux tools.
