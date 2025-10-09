# Changelog

All notable changes to this project will be documented in this file.

---

## [1.9.4] - 2025-10-09

### Added
- **ship_tracker** tool: Real-time vessel tracking via AIS data (AISStream.io WebSocket)
  - **track_ships**: Find ships in geographic area with filters (type, size, speed, status)
  - **get_ship_details**: Get detailed ship info by MMSI number
  - **get_port_traffic**: Monitor traffic near major ports
  - Real-time WebSocket connection to AISStream.io (free API)
  - Configurable timeout (3-60s) to control data collection duration
  - Advanced filtering: ship type, length, speed, navigation status
  - Major ports database (Rotterdam, Singapore, Le Havre, Hamburg, etc.)
  - Distance calculation with Haversine formula
  - Automatic deduplication by MMSI
  - Complete ship data: position, speed, heading, destination, ETA, dimensions
  - Support for all AIS ship types and navigation statuses
  - Architecture: `_ship_tracker/` (api, core, validators, utils, services/aisstream)

### Changed
- Tool count: 23 → **24 tools**
- `.env.example`: Added `AISSTREAM_API_KEY` with setup instructions

### Fixed
- `_ship_tracker/services/__init__.py`: Created missing package marker file
- WebSocket bounding box format: corrected to `[lat, lon]` instead of `[lon, lat]`

### Use Cases
- Monitor port traffic in real-time (Rotterdam, Singapore, Le Havre, etc.)
- Track cargo ships in specific areas
- Find vessels by speed, type, or navigation status
- Get live ship positions with sub-minute accuracy
- Maritime traffic analysis and monitoring

### Performance
- Typical response time: timeout + 2 seconds (WebSocket overhead)
- Ships emit AIS every 2-10 seconds (moving) or 3 minutes (anchored)
- Recommended timeouts: 10s (quick), 15-30s (standard), 60s (comprehensive)

### Coverage
- Coastal coverage: ~200 km from shore (AIS receivers)
- Best coverage: Major shipping lanes, ports, coastal areas
- No mid-ocean coverage (requires satellite AIS)

---

## [1.9.3] - 2025-10-09

### Added
- **youtube_search** tool: Search YouTube videos, channels, and playlists via YouTube Data API v3
  - **search**: Find videos/channels/playlists by keyword with advanced filters (order, type, region, safe search)
  - **get_video_details**: Get complete video information (title, description, views, likes, comments, duration, tags, thumbnails)
  - **get_trending**: Get trending videos by region and category
  - Official YouTube Data API v3 integration (free, 10,000 units/day)
  - Search = 100 units (~100 searches/day), video details = 1 unit (~10,000 requests/day)
  - Complete workflow: youtube_search → youtube_download → video_transcribe
  - Architecture: `_youtube_search/` (api, core, validators, services/youtube_api)
  - Comprehensive README with examples and quota management tips
  - Enhanced error messages with detailed API error reporting

### Changed
- Tool count: 22 → **23 tools**
- `.env.example`: Added `YOUTUBE_API_KEY` with setup instructions
- Error handling: Improved YouTube API error messages (quota exceeded, invalid API key, etc.)
- Documentation: Simplified, removed redundant ENV_VARIABLES.md (all documentation now in .env.example)

### Use Cases
- Search for specific videos or channels before downloading
- Research trending topics by region and category
- Get video metadata without downloading (duration, views, likes)
- Build video recommendation systems
- Analyze YouTube content at scale

### Workflow Integration
```bash
# 1. Search for videos
youtube_search → returns URLs and metadata

# 2. Download audio
youtube_download → saves to docs/video/

# 3. Transcribe
video_transcribe → returns transcript text
```

---

## [1.9.2] - 2025-10-09

### Added
- **aviation_weather** tool: upper air weather data via Open-Meteo API (free, no API key)
  - **get_winds_aloft**: Wind speed, direction, and temperature at specific altitude/coordinates
  - **calculate_tas**: Calculate True Airspeed from ground speed and wind
  - Supports all flight levels (1000-20000m / FL30-FL650)
  - Automatic pressure level conversion (1000, 925, 850, 700, 600, 500, 400, 300, 250, 225, 200, 150, 100, 70, 50, 30, 20, 10 hPa)
  - Unit conversions: km/h ↔ knots, meters ↔ feet, °C ↔ °F
  - Wind components: headwind/tailwind, crosswind
  - Real-time weather data (hourly forecasts)
  - No authentication required (Open-Meteo public API)
  - Architecture: `_aviation_weather/` (api, core, validators, utils, services/openmeteo)

### Changed
- Tool count: 21 → **22 tools**

### Use Cases
- Explain aircraft speed records (why ground speed differs from true airspeed)
- Flight planning (check winds at cruise altitude)
- Performance analysis (calculate TAS with wind correction)
- Integration with flight_tracker (enrich flight data with weather)

---

## [1.9.1] - 2025-10-08

### Added
- **flight_tracker** tool: real-time aircraft tracking via OpenSky Network API
  - Track flights by position (lat/lon) + radius (1-500 km)
  - Filters: altitude min/max, speed min/max, on_ground/in_flight, countries, callsign pattern
  - Automatic flight phase detection: cruise, climb, descent, approach, final_approach, landing_imminent
  - Sort by: distance, altitude, speed, callsign
  - Calculate distance with Haversine formula (circular search, not rectangular bbox)
  - Returns: position, speed, heading, vertical rate, country (registration), squawk, last contact
  - No authentication required (public API)
  - Architecture: `_flight_tracker/` (api, core, validators, utils, services/opensky)

### Fixed
- http_client: timeout maximum 300s → 600s (spec JSON + validator Python)

### Changed
- CHANGELOG.md: restructured for conciseness (28.7KB → 5.9KB, -79%)
- LLM_DEV_GUIDE.md: simplified (21.2KB → 5.8KB, -73%)
  - Removed redundant sections and verbose explanations
  - 10 focused sections vs 17 before
  - Direct bullet points, no repetition
- Tool count: 20 → **21 tools**

---

## [1.9.0] - 2025-10-08

### Added
- **youtube_download** tool: download video/audio from YouTube URLs
  - Modes: audio (MP3), video (MP4), both
  - URL validation, filename sanitization, unique naming
  - Metadata extraction (title, duration, uploader, views)
  - Duration limits, timeout control
  - Chroot: `docs/video/`

### Changed
- Tool count: 19 → 20

---

## [1.8.0] - 2025-10-08

### Added
- **video_transcribe** tool: FFmpeg audio extraction + Whisper API transcription
  - Parallel processing: 3 chunks simultanés (3x plus rapide)
  - Performance: 3 min vidéo → 20s traitement
  - Segmentation: `time_start`/`time_end` pour grosses vidéos
  - Retour: segments avec timestamps + texte complet
  - Chroot: `docs/video/`

### Fixed
- config.py: syntax error in `_read_env_dict()` (`Dict[str, str] = {}` → `data = {}`)
- Whisper client: SSL verification disabled for dev environment

### Changed
- Tool count: 18 → 19

---

## [1.7.1] - 2025-10-08

### Fixed
- Endpoint `HEAD /tools` manquant (polling ETag → erreur 405)
- Logs applicatifs invisibles (ajout `logging.basicConfig()`)
- Duplication logs HTTP (désactivation logs Uvicorn)

### Added
- Logs d'exécution enrichis: displayName + timing (ms) + émojis (🔧 ✅ ❌ ⏱️)

---

## [1.7.0] - 2025-10-08

### Added
- Panneau de contrôle moderne: layout 2 colonnes, sidebar, logo HD
- Configuration générique: lecture/modification automatique de toutes variables `.env`
- Hot-reload: 90% des variables sans restart
- Masquage total des secrets: `••••••••` (OWASP compliant)
- Documentation: `.env.example` with comprehensive comments

### Changed
- UX: un seul tool visible, search bar, badges colorés (present/absent)
- 32 variables documentées (Serveur, LLM, Git, IMAP, Vélib', JSON, Academic, Script)

### Security
- Secrets: zéro caractère exposé (avant: `****BkcD`)

---

## [1.6.0] - 2025-10-08

### Added
- **http_client** tool: universal REST/API client
  - Méthodes: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
  - Auth: Basic, Bearer, API Key
  - Body: JSON, Form data, Raw
  - Features: retry avec backoff, proxy, timeout, SSL verification
  - Response parsing: auto-detect, JSON, text, raw

### Changed
- Tool count: 17 → 18

---

## [1.5.0] - 2025-10-08

### Added
- **velib** tool: Vélib' Métropole Paris bike-sharing
  - Cache SQLite: ~1494 stations (station_code, name, lat, lon, capacity)
  - Temps réel: disponibilité vélos mécaniques/électriques, places libres
  - 3 opérations: refresh_stations, get_availability, check_cache
  - Intégration: `sqlite_db` pour recherches complexes

### Changed
- Tool count: 16 → 17

---

## [1.4.0] - 2025-10-08

### Added
- **pdf_download** tool: téléchargement PDF depuis URLs
  - Validation: magic bytes `%PDF-`
  - Métadonnées: pages, titre, auteur (pypdf)
  - Unique naming: suffixes `_1`, `_2`, etc.
  - Timeout: 5-300s (défaut 60s)
  - Chroot: `docs/pdfs`

### Changed
- Tool count: 15 → 16

---

## [1.3.0] - 2025-10-08

### Added
- **imap** tool: multi-account email access
  - 6 providers: Gmail, Outlook, Yahoo, iCloud, Infomaniak, Custom
  - Variables env séparées: `IMAP_<PROVIDER>_EMAIL`, `IMAP_<PROVIDER>_PASSWORD`
  - 13 opérations: connect, list_folders, search, get, download, mark (read/unread/spam), move, delete (batch)
  - Chroot: `files/imap/`

- **git** tool: enhanced operations
  - Nouvelles ops: fetch, pull, rebase, log, remote_info
  - Détection de conflits avec hints
  - Support: `--prune`, `--ff-only`, rebase continue/abort/skip

### Changed
- Tool count: 14 → 15

---

## [1.2.0] - 2025-10-08

### Added
- **ffmpeg_frames**: native PyAV frame-by-frame detection
  - Moving average + hysteresis + NMS + refinement
  - Per-frame debug: temps, diff, similarité%
  - Haute précision sur vidéos compressées
  - Export: images + timestamps + debug.json

### Changed
- Defaults: scale 96x96, ma_window 1, threshold_floor 0.05, NMS 0.2s, refine_window 0.5s, min_scene_frames 3

### Fixed
- Détection des hard cuts (downsampled CLI manquait beaucoup de coupes)

---

## [1.1.0] - 2025-10-08

### Added
- **ffmpeg_frames** tool: extraction de frames vidéo via FFmpeg
- Safe JSON: `safe_json.py` (NaN/Infinity/grands entiers sanitisés)
- Tool discovery: `tool_discovery.py` (auto-reload)
- Math tool: dispatcher refactorisé
  - Opérations de base: arithmétique, trig, log, exp, sqrt (erreurs explicites)
  - Opérations avancées: symbolique, calcul, algèbre linéaire, probas, polynômes, solveurs, nombres premiers, séries

### Changed
- Scripts dev: sourcing `.env`, vérification Python 3.11+, installation deps
- README: outils complets, endpoints, sécurité

### Fixed
- Math tool: erreurs HTTP 500 génériques → messages explicites
- `.env` chargé par app et scripts dev

### Security
- `.gitignore`: `docs/`, `files/`, `script_executor/`, `sqlite3/`, `venv/`, `.venv/`, `.DS_Store`, `__pycache__/`, `*.pyc`

---

## [1.0.0] - Initial release

### Core
- FastAPI server with MCP tools discovery
- Auto-reload tools from `src/tools/`
- Safe JSON serialization (NaN, Infinity, bigints)
- Panneau de contrôle web
- Configuration via `.env`

### Tools (14)
- call_llm: LLM orchestrator (2 phases, streaming)
- academic_research_super: recherche multi-sources (arXiv, PubMed, CrossRef, HAL)
- script_executor: sandbox Python sécurisé
- git: GitHub API + Git local
- gitbook: discovery et search
- sqlite_db: SQLite avec chroot
- pdf_search, pdf2text: manipulation PDF
- universal_doc_scraper: scraping documentation
- math: calcul avancé (numérique, symbolique, stats, algèbre linéaire)
- date: manipulation dates
- discord_webhook: publication Discord
- reddit_intelligence: scraping/analyse Reddit
