# 🧰 Dragonfly Tools Catalog (auto‑généré)

Ce fichier est généré automatiquement par `scripts/generate_tools_catalog.py`. Ne pas éditer à la main.

Total tools: 69

## 📊 Intelligence & Orchestration (10)

- Agent (Multi-turn v2) — Multi-turn LLM agent with automatic tool chaining. Simplified architecture with client-side state management. Supports conversation conti… · Tags: llm, agent, multi-turn, orchestration, autonomous, state
  - Opérations: N/A
  - Tokens: aucun

- Call LLM+tools — Appelle un modèle LLM en streaming. Orchestration tool_calls (MCP) en 2 phases. Supporte l'entrée multi-modale (images) via messages Open… · Tags: llm, orchestration, vision, multimodal
  - Opérations: N/A
  - Tokens: aucun

- Chat Agent (Threaded) — Agent conversationnel persistant avec exécution d'outils. Utilise l'API Threads pour stocker l'historique complet côté serveur. Idéal pou… · Tags: llm, agent, threading, multi-turn, conversation, persistent
  - Opérations: N/A
  - Tokens: aucun

- LLM Agent (Multi-turn) — Appelle un LLM avec capacité d'enchaînement automatique de tools. Le LLM peut appeler plusieurs tools en séquence, en utilisant les résul… · Tags: llm, agent, orchestration, multi-turn, chain, autonomous, resume, threading
  - Opérations: N/A
  - Tokens: aucun

- LLM Agent Planner — Orchestrateur LLM avec planification explicite. Génère un plan d'exécution structuré, optimise les parallélisations, puis exécute les éta… · Tags: llm, agent, planning, orchestration, reasoning, multi-step, workflow
  - Opérations: N/A
  - Tokens: aucun

- News Aggregator — Agrégateur d'actualités multi-sources (NewsAPI free tier limité, NYT, Guardian). IMPORTANT: NewsAPI free tier supporte UNIQUEMENT 'top_he… · Tags: external_sources, knowledge, search
  - Opérations: search_news, top_headlines, list_sources
  - Tokens: aucun

- Ollama Local + Web Search — Interface avec Ollama local (localhost:11434) + recherche web cloud. Gestion modèles, génération, chat, embeddings, recherche web. IMPORT…
  - Opérations: list_models, get_version, get_running_models, show_model, pull_model, push_model …
  - Tokens: aucun

- Python Orchestrator — Run Python-defined workflows (Process/SubGraphs/Steps). Start/stop/status/debug; graph extraction; validate; transforms; config. Nouveau… · Tags: process, python, debug
  - Opérations: start, stop, status, debug, observe, list …
  - Tokens: aucun

- Research — Recherche académique multi-sources (PubMed, arXiv, HAL, CrossRef). · Tags: knowledge, research, external_sources
  - Opérations: search_papers, get_paper_details, search_authors, get_citations
  - Tokens: aucun

- Voice Chat (Portal + Whisper + LLM) — Basculer la conversation courante en mode vocal local: capture micro (détection de silence), transcription Whisper (modèle par défaut), a… · Tags: voice, blocking, interactive
  - Opérations: N/A
  - Tokens: aucun

## 🔧 Development (9)

- Dev Navigator — Couteau suisse LLM pour explorer un dépôt: overview, tree, search, outline, open (plan fs_requests uniquement — pas de contenu), endpoint… · Tags: knowledge
  - Opérations: compose, overview, tree, search, outline, open …
  - Tokens: aucun

- Git — Git et GitHub unifiés. Opérations locales (commit, push, pull, rebase) et GitHub API (repos, branches, releases).
  - Opérations: ensure_repo, config_user, set_remote, sync_repo, status, fetch …
  - Tokens: aucun

- GitBook — Recherche et exploration de documentation GitBook. Découverte automatique de pages, recherche globale sans connaître les URLs. · Tags: knowledge, docs, search
  - Opérations: find_docs, extract_base_url, discover_site, search_site, read_page
  - Tokens: aucun

- I18n files manager — Liste les langues et gère les clés i18n (JSON et ES modules). Opérations en masse: ajout, modification, suppression et renommage de clés. · Tags: files, i18n
  - Opérations: list_langs, get_keys, upsert_keys, delete_keys, rename_key, upsert_key_all_langs
  - Tokens: aucun

- Playwright (Record & Play) — Enregistre une navigation via Playwright codegen (process.json live) et rejoue par ID (tout, jusqu’à une étape, ou une étape). Tous les f… · Tags: browser, record, replay
  - Opérations: record_start, record_list, record_delete, play
  - Tokens: aucun

- Python Sandbox — Exécute du code Python dans un sandbox sécurisé avec accès à des tools MCP. Pas d'imports, API limitée, timeout configurable.
  - Opérations: N/A
  - Tokens: aucun

- Shell Command — Execute shell commands (bash/sh). Useful for running scripts, tests, git commands, file operations. Supports piping, redirections, and wo… · Tags: shell, bash, command, exec, system
  - Opérations: N/A
  - Tokens: aucun

- Tool Audit — Audit lecture-seule d’un tool MCP: périmètre strict au tool, contexte complet pour LLM, multi-profils (perf, quality, maintain, invariant… · Tags: quality, performance, maintainability
  - Opérations: audit_tool
  - Tokens: aucun

- VS Code Control — Contrôle local de VS Code via la CLI 'code' et opérations de workspace: ouvrir fichiers/dossiers, diff, extensions, settings, recherche,… · Tags: vscode, editor, cli, local
  - Opérations: open_file, open_folder, diff_files, goto_line, list_extensions, install_extension …
  - Tokens: aucun

## 📧 Communication (6)

- Discord Bot — Client Discord Bot complet (REST API). Gestion messages, channels, threads, reactions, search. Requiert DISCORD_BOT_TOKEN. 29 opérations… · Tags: discord, bot, messaging, api
  - Opérations: list_guilds, list_messages, get_message, send_message, edit_message, delete_message …
  - Tokens: aucun

- Discord Webhook — Publie et gère des articles sous forme d'Embeds sur Discord via un webhook global (DISCORD_WEBHOOK_URL). Supporte create/update/upsert/de…
  - Opérations: create, update, upsert, delete, get, list …
  - Tokens: aucun

- Email Send (SMTP) — Envoyer des emails via SMTP (Gmail ou Infomaniak). Supporte texte/HTML, pièces jointes, CC/BCC, priorité.
  - Opérations: send, test_connection
  - Tokens: aucun

- IMAP Email — Accès emails via IMAP (Gmail, Outlook, Yahoo, iCloud, Infomaniak, serveurs custom). Recherche, lecture, téléchargement pièces jointes, ma…
  - Opérations: connect, list_folders, search_messages, get_message, download_attachments, mark_read …
  - Tokens: aucun

- Mail Manager Background — Surveille des boites IMAP en tâche de fond, lit le mail entier (cap 30ko), sanitize, classifie via call_llm (modèle paramétrable), déplac… · Tags: async, background, graph, imap, email
  - Opérations: start, stop, status
  - Tokens: aucun

- Telegram Bot — Complete Telegram Bot API access. Send messages (text, photos, documents, videos, locations), read updates, edit/delete messages, polls.… · Tags: telegram, messaging, bot, notifications
  - Opérations: send_message, send_photo, send_document, send_location, send_video, get_updates …
  - Tokens: aucun

## 🗄️ Data & Storage (4)

- CoinGecko — Complete cryptocurrency data via CoinGecko API. Prices, market data, historical charts, trending coins, exchanges. Free tier: 50 calls/mi… · Tags: crypto, cryptocurrency, prices, market_data
  - Opérations: get_price, get_coin_info, search_coins, get_market_chart, get_trending, get_global_data …
  - Tokens: aucun

- Excel Row — Insert, update, delete rows in Excel with advanced formatting (row-level and per-column overrides), backups, and restore. · Tags: excel, spreadsheet, formatting
  - Opérations: insert_row, update_row, delete_row, list_backups, restore_backup
  - Tokens: aucun

- Excel to SQLite — Import Excel (.xlsx) data into SQLite database with automatic schema detection, type mapping, and batch processing
  - Opérations: import_excel, preview, get_sheets, validate_mapping, get_info
  - Tokens: aucun

- SQLite Database — Gestion d'une base SQLite locale dans <projet>/sqlite3. Créer, lister, supprimer des DB et exécuter des requêtes SQL. · Tags: sqlite, database, sql, local_storage
  - Opérations: ensure_dir, list_dbs, create_db, delete_db, get_tables, describe …
  - Tokens: aucun

## 📄 Documents (9)

- Doc Scraper — Universal documentation scraper supporting GitBook, Notion, Confluence, ReadTheDocs, Docusaurus, and other doc platforms. Discover, extra…
  - Opérations: discover_docs, extract_page, search_across_sites, detect_platform
  - Tokens: aucun

- Légifrance Consult — Consultation du corpus juridique français (LEGI).

[DEUX STRATEGIES PRINCIPALES]

[STRATEGIE A] NAVIGATION PURE (Recommandée pour explora… · Tags: external_sources, knowledge, legal, france
  - Opérations: search_sections, get_section_tree, get_articles
  - Tokens: aucun

- Légifrance Consult — Consultation du corpus juridique français (LEGI). 3 opérations : search_sections (recherche textuelle), get_section_tree (arborescence av… · Tags: external_sources, knowledge, legal, france
  - Opérations: search_sections, get_section_tree, get_articles
  - Tokens: aucun

- Légifrance LEGI v2 — Accès aux codes juridiques français (corpus LEGI). 3 opérations : list_codes (liste des codes avec métadonnées, filtrable par nature), ge… · Tags: external_sources, knowledge, legal, france
  - Opérations: list_codes, get_code, get_articles
  - Tokens: aucun

- Légifrance LEGI v2 - Optimisé — Accès aux codes juridiques français (corpus LEGI). WORKFLOW RECOMMANDÉ : (1) list_codes UNE FOIS pour identifier le code → (2) get_code a… · Tags: external_sources, knowledge, legal, france
  - Opérations: list_codes, get_code, get_articles
  - Tokens: aucun

- Office to PDF Converter — Convert Microsoft Office documents (Word, PowerPoint) to PDF using either the Office suite installed on the laptop (via docx2pdf) or a he…
  - Opérations: convert, get_info
  - Tokens: aucun

- PDF Download — Télécharge un fichier PDF depuis une URL et le sauvegarde dans docs/pdfs. Gère automatiquement les conflits de noms avec suffixes numériq…
  - Opérations: download
  - Tokens: aucun

- PDF Search — Recherche texte dans un ou plusieurs PDFs. Hard cap à 50 résultats détaillés, affiche le total trouvé. Supporte regex, pages, récursif. · Tags: search, pdf, text
  - Opérations: search
  - Tokens: aucun

- PDF to Text — Extraction de texte depuis un PDF pour des pages données. Entrée: path (string), pages (string optionnelle) — Sortie: texte concaténé et…
  - Opérations: N/A
  - Tokens: aucun

## 🎬 Media (9)

- FFmpeg Frames — Extraction d'images d'une vidéo: détection automatique des plans (similarité) + début/fin + samples intraplans.
  - Opérations: extract_frames
  - Tokens: aucun

- Gemini Image Studio — Génère ou édite des images avec gemini-2.5-flash-image-preview. Entrées: URLs http(s), fichiers locaux (./docs), data URLs, ou base64 bru…
  - Opérations: generate, edit
  - Tokens: aucun

- Google Veo 3.1 Video — Créer et gérer des rendus vidéo avec Google Veo 3.1 (texte→vidéo, image→vidéo, images de référence ≤3, interpolation première/dernière im… · Tags: external_sources, video, generation
  - Opérations: create, get_status, download, extend, auto_start
  - Tokens: aucun

- Kling Video (Text/Image/Multi-Image) — Create and manage video renders with Kling API (text2video, image2video incl. start/end on v2.1 Pro, multi-image2video). Asynchronous cre… · Tags: external_sources, video, generation, kling
  - Opérations: create, get_status, list, download, auto_start
  - Tokens: aucun

- Media Transcription (Audio/Video) — Transcribe an audio or video file from docs/audio or docs/video using the Whisper API. Supports time-based segmentation and parallel proc… · Tags: media, audio, video, transcription, whisper
  - Opérations: transcribe, get_info
  - Tokens: aucun

- OBS Control — Contrôle OBS via une seule fonction multi-actions en appels courts (ou sessions courtes). Pas d’API fichiers: si un média local est requi…
  - Opérations: N/A
  - Tokens: aucun

- OpenAI Video (Sora) — Create and manage video renders with OpenAI's Sora models (sora-2 / sora-2-pro). Supports create (with optional wait), get_status, downlo… · Tags: external_sources, video, generation
  - Opérations: create, get_status, download, list, delete, remix …
  - Tokens: aucun

- YouTube Downloader — Download videos or audio from YouTube URLs. Supports audio-only (for transcription), video, or both. Files saved to docs/video/ for integ… · Tags: youtube, video, audio, download, transcription
  - Opérations: download, get_info
  - Tokens: aucun

- YouTube Search — Rechercher vidéos, chaînes et playlists YouTube. Filtres : date, popularité, région, safe search.
  - Opérations: search, get_video_details, get_trending
  - Tokens: aucun

## ✈️ Transportation (4)

- Aviation Weather — Get upper air weather data (winds, temperature) at specific altitude and coordinates using Open-Meteo API. Useful for flight planning and… · Tags: weather, aviation, flight
  - Opérations: get_winds_aloft, calculate_tas
  - Tokens: aucun

- Flight Tracker — Track aircraft in real-time using OpenSky Network API. Filter by position, radius, altitude, speed, country. Get live position, speed, he…
  - Opérations: track_flights
  - Tokens: aucun

- Ship Tracker — Suivi navires temps réel via AIS. Position, vitesse, cap, destination, type navire. Recherche par zone, MMSI ou port.
  - Opérations: track_ships, get_ship_details, get_port_traffic
  - Tokens: aucun

- Vélib' Métropole — Gestionnaire de cache Vélib' Métropole (Paris). Rafraîchit les données statiques des stations (stockées en SQLite), récupère la disponibi… · Tags: paris, bike_sharing, transport, realtime
  - Opérations: refresh_stations, get_availability, check_cache
  - Tokens: aucun

## 🌐 Networking (3)

- HTTP Client — Client HTTP/REST générique pour interagir avec n'importe quelle API. Supporte GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS avec authentif…
  - Opérations: N/A
  - Tokens: aucun

- SSH Client — Client SSH/SFTP universel pour exécuter des commandes à distance, transférer des fichiers (upload/download), et gérer des serveurs. Suppo… · Tags: remote, server, automation
  - Opérations: exec, upload, download, status
  - Tokens: aucun

- SSH Diagnostics — Outil de diagnostic pour connexions SSH instables. Permet de tester la connectivité, analyser les logs serveur, vérifier les keepalives,… · Tags: diagnostics, ssh, network, troubleshooting
  - Opérations: test_connection, check_server_logs, check_keepalive_config, test_network, check_firewall, check_fail2ban …
  - Tokens: aucun

## 🔢 Utilities (8)

- Date/Time — Common date/time operations: weekday name, difference between dates, now/today, add duration, format, parse, week number. Supports timezo… · Tags: datetime, calendar, timezone
  - Opérations: now, today, day_of_week, diff, diff_days, add …
  - Tokens: aucun

- Device Location — Get GPS coordinates and location information for the current device based on network/IP geolocation. Returns latitude, longitude, city, r… · Tags: location, gps, network, geo
  - Opérations: get_location
  - Tokens: aucun

- Google Maps — Complete Google Maps API access. Geocoding, directions, places search, distance matrix, timezone, elevation. Free tier: $200 credit/month… · Tags: maps, geocoding, directions, places, navigation
  - Opérations: geocode, reverse_geocode, directions, distance_matrix, places_search, place_details …
  - Tokens: aucun

- Host Audit — Plans d'audit compacts pour macOS (local) et hôtes distants via SSH: Ubuntu, Nginx, Apache, PHP-FPM, Node.js, MySQL, Symfony. Ne lance pa… · Tags: system, audit, ssh, os, mysql, symfony
  - Opérations: macos_local, ubuntu_ssh_plan, mysql_ssh_plan, symfony_ssh_plan, nginx_ssh_plan, apache_ssh_plan …
  - Tokens: aucun

- Math — Maths: arithmétique (précision arbitr.), expressions (SymPy), symbolique, complexes, probas (suppl.), algèbre linéaire (+ext), solveurs,…
  - Opérations: add, subtract, multiply, divide, power, modulo …
  - Tokens: aucun

- Open-Meteo — Complete weather data via Open-Meteo API (open source). Current weather, hourly/daily forecasts, air quality, geocoding. 100% free, no AP… · Tags: weather, forecast, air_quality, free
  - Opérations: current_weather, forecast_hourly, forecast_daily, air_quality, geocoding, reverse_geocoding
  - Tokens: aucun

- Random Numbers — Générateur nombres aléatoires VRAIS (bruit atmosphérique RANDOM.ORG). Fallback CSPRNG si échec. Output MINIMAL. · Tags: randomness, physical
  - Opérations: generate_integers, generate_floats, generate_bytes, coin_flip, dice_roll, shuffle …
  - Tokens: aucun

- SSH Admin — Administration et audit de serveurs distants via SSH (authentification par clés SSH uniquement). Permet d'exécuter des commandes/scripts… · Tags: system, admin, ssh, devops
  - Opérations: connect, exec, exec_file, upload, download
  - Tokens: aucun

## 🎮 Social & Entertainment (7)

- Astronomy & Space — Complete astronomy calculations using Skyfield (100% local, no API key required). Planet positions, moon phases, ephemeris, celestial eve… · Tags: space, astronomy, science, educational, planets, stars
  - Opérations: planet_position, moon_phase, sun_moon_times, celestial_events, planet_info, visible_planets …
  - Tokens: aucun

- Chess.com — Access Chess.com public data API - player profiles, games, stats, clubs, tournaments, matches, countries, leaderboards, puzzles, streamer…
  - Opérations: get_player_profile, get_player_stats, get_player_games_current, get_player_games_archives_list, get_player_games_archives, get_player_clubs …
  - Tokens: aucun

- Lichess (Public API) — Accès en lecture seule aux endpoints publics de Lichess: profils, perfs, équipes, parties, tournois, leaderboards, puzzles. Sans authenti… · Tags: chess, lichess, public_api
  - Opérations: get_user_profile, get_user_perfs, get_user_teams, get_user_current_game, get_user_games, get_team_details …
  - Tokens: aucun

- Minecraft Control — Control Minecraft server via RCON: execute commands, spawn entities, build structures, import 3D models, control player, manage environment. · Tags: gaming, 3d, scripting, rcon
  - Opérations: execute_command, spawn_entities, build_structure, import_3d_model, control_player, set_environment …
  - Tokens: aucun

- Reddit — Advanced Reddit analysis tool. Search subreddits, analyze sentiment, find experts, track trends, get post comments. Discover insights fro… · Tags: social, knowledge, scraping, external_sources
  - Opérations: search_subreddit, get_comments, analyze_sentiment, find_trending, find_experts, multi_search
  - Tokens: aucun

- Stockfish (Auto-75) — Évalue une position ou analyse une partie avec Stockfish en autoconfigurant ~75% des ressources (Threads/Hash). Pour analyze_game, un bud… · Tags: chess, uci, auto-tune
  - Opérations: evaluate_position, analyze_game
  - Tokens: aucun

- Trivia API — Complete Open Trivia Database API access. Get trivia questions, manage categories, session tokens. 100% free, no API key required. Suppor… · Tags: quiz, games, educational, trivia
  - Opérations: get_questions, list_categories, get_category_count, get_global_count, create_session_token, reset_session_token
  - Tokens: aucun
