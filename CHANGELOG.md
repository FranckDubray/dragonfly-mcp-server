# Changelog

All notable changes to this project will be documented in this file.

---

## [1.9.0] - 2025-10-08

### 🎉 Highlights
- **Nouveau tool youtube_download** : téléchargement vidéos/audio YouTube
- **Workflow complet transcription** : YouTube → Audio → Whisper
- **Intégration parfaite video_transcribe** : pipeline automatisé
- **Tool count** : 20 tools disponibles (19→20)

### ✨ Added

#### YouTube Download Tool 🆕
- **Nouveau tool** : `youtube_download` pour télécharger depuis YouTube
- **Opérations** :
  - `download` : Télécharge vidéo/audio (MP3 ou MP4)
  - `get_info` : Récupère métadonnées sans télécharger
- **Paramètres flexibles** :
  - `media_type`: **"audio"** (MP3, parfait transcription), "video" (MP4), "both" (séparés)
  - `quality`: "best", "720p", "480p", "360p"
  - `filename`: custom ou auto depuis titre vidéo
  - `max_duration`: 7200s défaut (2h max)
  - `timeout`: 300s défaut (5-600s)
- **Features** :
  - Validation URL YouTube (tous formats supportés)
  - Filename sanitization automatique
  - Unique naming (_1, _2 si fichier existe)
  - Duration check (évite téléchargements massifs)
  - Metadata extraction (titre, durée, uploader, vues)
- **Sécurité** :
  - Chroot à `docs/video/`
  - URL validation stricte (YouTube domains uniquement)
  - Filename sanitization (pas de path traversal)
  - Duration limits configurables
  - Timeout enforcement
- **Architecture** : `_youtube_download/` (api, core, validators, utils, services/downloader)
- **Spec** : `src/tool_specs/youtube_download.json` (source de vérité canonique)
- **Dépendance** : `yt-dlp>=2023.10.0` (déjà présent dans pyproject.toml)

#### Workflow Intégré 🔗
```bash
# 1. Télécharger audio YouTube (rapide, léger)
youtube_download(url="...", media_type="audio")
# → docs/video/Ma_Video.mp3

# 2. Transcrire avec Whisper (parallèle 3x)
video_transcribe(path="docs/video/Ma_Video.mp3")
# → Transcription complète exploitable !
```

#### Documentation complète 🆕
- **src/tools/_youtube_download/README.md** : documentation détaillée (9KB)
  - Features et sécurité
  - Use cases (transcription, archive, analyse)
  - Architecture et configuration
  - Exemples complets (audio, vidéo, both)
  - Performance tips
  - Error handling
- **Spec JSON** : youtube_download.json avec validation complète

### 🎯 Use Cases

**1. Conférences tech → Transcription**
```json
{"url": "https://youtube.com/watch?v=...", "media_type": "audio"}
```

**2. Tutoriels → Archive texte searchable**
```json
{"url": "...", "media_type": "both", "quality": "720p"}
```

**3. Podcasts vidéo → Extraction citations**
```json
{"url": "...", "media_type": "audio", "filename": "podcast_ep42"}
```

**4. Check info avant download**
```json
{"operation": "get_info", "url": "..."}
# → durée, titre, vues, etc.
```

### 🔄 Changed
- Tool count : 19 → **20 tools**
- Dépendance `yt-dlp` déjà présente dans pyproject.toml

### 📚 Documentation
- Ajout section youtube_download dans README principal
- Mise à jour src/tools/README.md (20 tools)
- Ajout src/tools/_youtube_download/README.md complet

### 🐛 Fixed
- Aucun bug fix (nouveau tool uniquement)

### 📦 Migration notes
- **Nouveau users** : Tool disponible immédiatement après `./scripts/dev.sh`
- **Existing users** : Restart serveur pour découvrir le tool
- **Dépendances** : `yt-dlp` déjà inclus, FFmpeg requis (système)
- **Configuration** : Aucune variable d'env requise (fonctionne out-of-the-box)

### 🎬 Test réussi
**Vidéo** : "Le Dîner de cons" - Il s'appelle Juste Leblanc (4min16s)
- ✅ Téléchargement audio : 5.9 MB en quelques secondes
- ✅ Transcription Whisper : ~20 secondes (parallèle 3x)
- ✅ 5 segments avec timestamps
- ✅ Transcription complète exploitable

---

## [1.8.0] - 2025-10-08

### 🎉 Highlights
- **Nouveau tool video_transcribe** : extraction audio + transcription Whisper API
- **Performance exceptionnelle** : 3 minutes de vidéo → 20 secondes de traitement
- **Parallélisation intelligente** : traitement par batch de 3 chunks simultanés
- **Segmentation temporelle** : time_start/time_end pour vidéos volumineuses
- **Tool count** : 19 tools disponibles (18→19)

### ✨ Added

#### Video Transcription Tool 🆕
- **Nouveau tool** : `video_transcribe` pour transcription audio de vidéos
- **Extraction audio** : FFmpeg extraction directe segment par segment (pas de fichiers temp persistants)
- **Whisper API** : intégration multipart/form-data avec `/api/v1/audio/transcriptions`
- **Parallélisation** : ThreadPoolExecutor avec max_workers=3 (traite 3 chunks en parallèle)
- **Performance** : 
  - Avant (séquentiel) : 3 min vidéo → ~65 secondes
  - Après (parallèle) : 3 min vidéo → **~20 secondes** ⚡
  - Gain : **3x plus rapide**
- **Segmentation temporelle** : 
  - `time_start`/`time_end` pour découper grosses vidéos
  - `chunk_duration` configurable (défaut 60s)
- **Retour JSON** : segments avec timestamps + texte complet + metadata
- **Opérations** :
  - `transcribe` : extraction audio + transcription Whisper
  - `get_info` : métadonnées vidéo (durée, codec audio)
- **Sécurité** :
  - Chroot à `docs/video/` pour fichiers source
  - Cleanup automatique des fichiers temp après chaque chunk
  - Validation complète des entrées (path, time ranges, chunk duration)
- **Architecture** : `_video_transcribe/` (api, core, audio_extractor, whisper_client, validators, utils)
- **Spec** : `src/tool_specs/video_transcribe.json` (source de vérité canonique)

#### Documentation complète 🆕
- **README.md** : section video_transcribe avec benchmarks performance
- **src/tools/README.md** : catalogue complet 19 tools avec détails techniques
- **src/tools/_video_transcribe/README.md** : documentation détaillée du tool
  - Features et performance
  - Use cases (vidéos courtes, segmentation grandes vidéos)
  - Architecture et configuration
  - Error handling et optimisation

### 🐛 Fixed

#### Syntax error in config.py
- **Fix** : Correction erreur syntaxe dans `_read_env_dict()`
- **Problème** : `Dict[str, str] = {}` (assignation à un type → invalide)
- **Solution** : `data = {}` (variable correcte)
- **Impact** : Endpoint `/config` crashait avec erreur 500
- **Commit** : 1089ecb

#### SSL verification in Whisper client
- **Fix** : Ajout `verify=False` pour environnement dev
- **Problème** : Certificat SSL auto-signé sur `dev-ai.dragonflygroup.fr`
- **Solution** : Désactivation vérification SSL (dev uniquement)
- **Commit** : c159c53

### 🔄 Changed
- Tool count : 18 → **19 tools**
- Performance transcription : gain 3x avec parallélisation
- Documentation mise à jour (3 README)

### 📊 Workflow de transcription

**Processus optimisé** :
1. FFmpeg extrait segment audio (0-60s) → temp file
2. Upload multipart vers Whisper API
3. Récupération transcription
4. Cleanup temp file immédiat
5. **Répétition en parallèle** (3 chunks à la fois)

**Exemple** (vidéo 3 minutes, 4 chunks) :
- Batch 1 : chunks [0-60s, 60-120s, 120-180s] en parallèle → 20s
- Batch 2 : chunk [180-183s] seul → 5s
- **Total : ~25 secondes** vs 65s séquentiel

### 📦 Migration notes
- **Nouveau users** : Démarrez avec `./scripts/dev.sh`, tool disponible immédiatement
- **Existing users** : No breaking changes, nouveau tool disponible
- **Configuration** : Variables requises `AI_PORTAL_TOKEN`, `LLM_ENDPOINT`
- **Dépendances** : FFmpeg requis (système), `requests` déjà dans dependencies
- **Restart** : Redémarrer le serveur pour découvrir le nouveau tool

### 🎯 Use cases video_transcribe

**Vidéo courte (< 10 minutes)** :
```json
{"operation": "transcribe", "path": "docs/video/demo.mp4"}
```

**Grosse vidéo (segmentation)** :
```json
// Première heure
{"path": "...", "time_start": 0, "time_end": 3600}

// Deuxième heure
{"path": "...", "time_start": 3600, "time_end": 7200}
```

---

## [1.7.1] - 2025-10-08

### 🎉 Highlights
- **Logs ultra-propres** : displayName + timing d'exécution sur chaque tool
- **Fix polling HEAD** : plus d'erreur 405 toutes les 5 secondes
- **Configuration logging** : logs applicatifs maintenant visibles
- **Désactivation logs Uvicorn** : évite duplication des logs HTTP

### 🐛 Fixed

#### Endpoint HEAD manquant
- **Fix**: Ajout du handler `@app.head("/tools")` pour le polling ETag
- **Problème** : Le panneau de contrôle faisait une requête HEAD toutes les 5s → erreur 405
- **Solution** : Endpoint HEAD qui calcule l'ETag sans payload (optimisation)
- **Commit** : 67bc960

#### Configuration du logging
- **Fix**: Ajout de `logging.basicConfig()` dans `server.py`
- **Problème** : Les logs custom de `app_factory.py` ne s'affichaient pas
- **Solution** : Configuration du logger avec StreamHandler avant import de l'app
- **Commit** : f3d6a6b

#### Duplication des logs HTTP
- **Chore**: Désactivation des logs d'accès Uvicorn (`access_log=False`)
- **Problème** : Logs HTTP apparaissaient en double (avant et après exécution)
- **Solution** : Utilisation exclusive des logs custom plus informatifs
- **Commit** : 5100be9

### ✨ Added

#### Logs d'exécution enrichis
- **Feature**: DisplayName + timing dans les logs d'exécution
- **Format** : `🔧 Executing 'Display Name' (technical_name)` → `✅ 'Display Name' completed in 0.123s`
- **Précision** : `time.perf_counter()` pour timing haute précision (microseconde)
- **Cas d'erreur** : Timing également affiché sur erreurs/timeouts pour debug
- **Commit** : 214d041

### 📊 Exemple de logs (avant/après)

**Avant v1.7.1** :
```
INFO:     127.0.0.1:51899 - "POST /execute HTTP/1.1" 200 OK
INFO:     127.0.0.1:51487 - "HEAD /tools HTTP/1.1" 405 Method Not Allowed  (× toutes les 5s)
```

**Après v1.7.1** :
```
🔧 Executing 'Date/Time' (date)
✅ 'Date/Time' completed in 0.003s
```

### 🔄 Changed
- Logs Uvicorn access désactivés (remplacés par logs custom)
- Format de logs unifié avec émojis (🔧 start, ✅ success, ❌ error, ⏱️ timeout)

### 📦 Migration notes
- **No breaking changes** : hotfix release compatible v1.7.0
- **Restart required** : pour bénéficier des nouveaux logs
- Tous les outils fonctionnent à l'identique

---

## [1.7.0] - 2025-10-08

### 🎉 Highlights
- **Refonte complète du panneau de contrôle** : design moderne sidebar + zone unique
- **Configuration générique et automatique** : toutes les variables du .env gérées dynamiquement
- **Hot-reload des variables** : 90% des variables modifiables sans restart
- **Masquage total des secrets** : zéro caractère exposé (sécurité OWASP)
- **Logo HD professionnel** : remplacement emoji par image de marque

### ✨ Added

#### Panneau de contrôle moderne 🆕
- **Layout 2 colonnes** : Sidebar (280px) + Zone de travail
- **Un seul tool visible** à la fois (fini le scroll dans tous les panneaux)
- **Search bar** : filtrage instantané des 18 tools
- **Logo HD Dragonfly** : image professionnelle (assets/LOGO_DRAGONFLY_HD.jpg)
- **Design épuré** : fond blanc, espacements aérés, animations smooth
- **Responsive** : mobile-ready avec sidebar collapsible
- **Zone de résultat** : max-height 400px avec scroll si nécessaire

#### Configuration générique et automatique 🆕
- **Lecture automatique** de toutes les variables du .env
- **Génération dynamique** des champs (nombre illimité de variables)
- **Détection automatique des secrets** (TOKEN, PASSWORD, KEY, SECRET, API)
- **Badges colorés** : vert (present) / rouge (absent)
- **Hot-reload** : 90% des variables sans restart du serveur
- **Interface modale** : accessible via bouton en bas de sidebar

#### Documentation complète 🆕
- **.env.example** : template complet avec 32+ variables documentées
- **ENV_VARIABLES.md** : guide utilisateur détaillé
  - Tableaux par catégorie (Serveur, LLM, Git, IMAP, Vélib', JSON, Academic, Script)
  - Section Hot-Reload (liste ✅/⚠️)
  - Quick Start et Troubleshooting
- **dev.sh** : copie automatique `.env.example` → `.env` si absent

### 🔄 Changed

#### UX améliorée
- **État actif clair** : border bleu + fond blanc sur tool sélectionné
- **Formulaire aéré** : labels, hints, required marks, enum hints
- **Bouton Execute** : gros, visible, avec effet hover/click
- **Résultats** : success (vert) / error (rouge) avec couleurs claires
- **Empty state** : message élégant au démarrage
- **Status bar** : feedback immédiat en haut (Loading, Success, Error)

#### Configuration
- **32 variables documentées** (Serveur 5, LLM 7, Git 1, IMAP 15, Vélib' 2, JSON 3, Academic 3, Script 1)
- **Documentation succincte** : commentaires courts, focus sur l'essentiel
- **RELOAD supprimé** : variable legacy remplacée par AUTO_RELOAD_TOOLS + ?reload=1

### 🔒 Security

#### Masquage total des secrets
- **Ancienne méthode** : `****BkcD` (derniers caractères visibles) ❌
- **Nouvelle méthode** : `••••••••••••••••` (masquage total) ✅
- **Bullets proportionnels** : indication de longueur (max 16 pour lisibilité)
- **OWASP compliant** : zéro information sur le contenu réel
- **Protection shoulder surfing** : impossible de voir quoi que ce soit

### 📚 Documentation
- README mis à jour : section Panneau de contrôle (v1.7.0)
- ENV_VARIABLES.md : guide complet des 32 variables
- .env.example : template prêt à l'emploi
- dev.sh : copie auto .env.example → .env

### 🐛 Fixed
- Secrets partiellement visibles dans le panneau de configuration
- Layout scroll désastreux avec tous les tools affichés
- Variables d'environnement hardcodées dans le panneau
- Confusion entre RELOAD (legacy) et AUTO_RELOAD_TOOLS

### 📦 Migration notes
- **Nouveau users** : `./scripts/dev.sh` crée automatiquement le `.env`
- **Existing users** : no breaking changes, nouveau panneau compatible
- **Hot-reload** : modifier via `/control` → Save → effet immédiat
- Variables nécessitant restart : `MCP_HOST`, `MCP_PORT`, `LOG_LEVEL`, `EXECUTE_TIMEOUT_SEC`, `AUTO_RELOAD_TOOLS`

---

## [1.6.0] - 2025-10-08

### 🎉 Highlights
- **HTTP Client Tool** for universal REST/API interactions
- All HTTP methods supported (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Complete authentication suite (Basic, Bearer, API Key)
- Retry logic with exponential backoff
- Production-ready error handling

### ✨ Added

#### HTTP Client Tool 🆕
- **New tool**: `http_client` for interacting with any REST/API
- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Authentication**:
  - Basic Auth (username + password)
  - Bearer Auth (JWT/token)
  - API Key (custom header)
- **Body formats**:
  - JSON (auto-serialized with Content-Type)
  - Form data (application/x-www-form-urlencoded)
  - Raw text/XML
- **Advanced features**:
  - Retry logic with exponential backoff (0-5 retries)
  - Configurable timeout (1-300s, default 30s)
  - Proxy support (HTTP/HTTPS/SOCKS5)
  - SSL verification toggle
  - Response parsing (auto-detect, JSON, text, raw)
  - Optional response saving to files/
  - Follow redirects (configurable)
- **Architecture**: `_http_client/` (api, core, auth, retry, validators, utils)
- **Spec**: `src/tool_specs/http_client.json` (canonical source of truth)
- **Security**:
  - URL validation (http/https only)
  - Timeout enforcement (prevents infinite hangs)
  - SSL verification enabled by default
  - Auth credentials masked in logs
  - Chroot saves to `files/http_responses/`

### 🔄 Changed
- Tool count increased from 17 to 18
- Enhanced networking & API integration capabilities
- **Improved UX**: Added user-friendly `displayName` to tool specs (SQLite Database, PDF Search, PDF to Text, Python Sandbox, etc.) for better tool discovery

### 📚 Documentation
- Updated main README with http_client tool (18 tools total)
- Added comprehensive README in `src/tools/_http_client/`
- Created HTTP_CLIENT_SUMMARY.md with complete specifications
- Enhanced tool specs with displayName for better UX

### 🐛 Fixed
- No bug fixes in this release (new feature only)

### 📦 Migration notes
- **New users**: Start using the tool immediately (see documentation)
- **Existing users**: No breaking changes, new HTTP client available
- Requires `requests` library (already in dependencies)

---

## [1.5.0] - 2025-10-08

### 🎉 Highlights
- **Vélib' Métropole Tool** for Paris bike-sharing data
- SQLite cache management for station data
- Real-time availability API integration
- Clean architecture with minimal tool scope

### ✨ Added

#### Vélib' Tool 🆕
- **New tool**: `velib` for managing Vélib' Métropole station data
- **Features**:
  - SQLite cache for ~1494 stations (static data)
  - Real-time availability API (bikes mechanical/electric, docks free)
  - 3 operations: `refresh_stations`, `get_availability`, `check_cache`
  - Integration with `sqlite_db` tool for complex searches
  - Open Data API (no authentication required)
- **Database schema**:
  - `station_code` (TEXT, PRIMARY KEY)
  - `station_id` (INTEGER, system ID)
  - `name` (TEXT, station name)
  - `lat`, `lon` (REAL, GPS coordinates)
  - `capacity` (INTEGER, total docks)
  - `station_opening_hours` (TEXT, usually null)
- **Architecture**: `_velib/` (api, core, db, fetcher, validators, utils)
- **Spec**: `src/tool_specs/velib.json` (canonical source of truth)
- **Security**:
  - SQLite chroot to `sqlite3/velib.db`
  - Input validation (station_code: alphanumeric, max 20 chars)
  - Parameterized queries (SQL injection protection)
  - HTTP timeout: 30s
  - No secrets required (public API)

### 📚 Documentation
- Updated main README with velib tool (17 tools total)
- Updated src/README.md with velib examples
- Updated src/tools/README.md with velib details
- Added comprehensive README in `src/tools/_velib/`
- Created VELIB_TOOL_SUMMARY.md with complete specifications

### 🔄 Changed
- Tool count increased from 16 to 17
- Enhanced transport & mobility capabilities

### 📦 Migration notes
- **New users**: Start using the tool immediately (see documentation)
- **Existing users**: No breaking changes, new transport feature available
- Vélib' data is public, no API key required
- First run requires `refresh_stations` to populate cache

---

## [1.4.0] - 2025-10-08

### 🎉 Highlights
- **PDF Download Tool** with automatic metadata extraction
- Intelligent filename management with unique naming
- Complete PDF workflow integration (download → extract → search)

### ✨ Added

#### PDF Download Tool 🆕
- **New tool**: `pdf_download` for downloading PDFs from URLs to `docs/pdfs`
- **Features**:
  - HTTP/HTTPS download with configurable timeout (5-300s, default 60s)
  - PDF validation via magic bytes (`%PDF-`)
  - **Automatic metadata extraction**: page count, title, author, creator
  - Automatic unique filename generation (suffixes `_1`, `_2`, etc.)
  - Optional overwrite mode
  - Filename extraction from URL if not provided
  - User-Agent header for compatibility
- **Security**:
  - Chroot to `docs/pdfs` directory
  - URL validation (http/https only)
  - Filename sanitization (no path traversal)
  - Magic bytes verification
- **Architecture**: `_pdf_download/` (api, core, validators, utils, services/downloader)
- **Spec**: `src/tool_specs/pdf_download.json` (canonical source of truth)

### 📚 Documentation
- Updated main README with pdf_download tool (16 tools total)
- Updated src/README.md with pdf_download examples
- Updated src/tools/README.md with complete tool catalog
- Added comprehensive README in `src/tools/_pdf_download/`

### 🔄 Changed
- Tool count increased from 15 to 16
- Enhanced PDF workflow capabilities

### 📦 Migration notes
- **New users**: Start using the tool immediately (see documentation)
- **Existing users**: No breaking changes, extends existing PDF capabilities
- Requires `pypdf>=4.2.0` (already in dependencies)

---

## [1.3.0] - 2025-10-08

### 🎉 Highlights
- **IMAP multi-account email tool** with 6 providers (Gmail, Outlook, Yahoo, iCloud, Infomaniak, Custom)
- **Git tool enhanced** with pull, fetch, rebase operations and conflict detection
- Complete workflow automation without manual CLI commands

### ✨ Added

#### IMAP Tool (multi-account email access)
- **Universal IMAP access** across 6 providers: Gmail, Outlook, Yahoo, iCloud, **Infomaniak** (new), Custom
- **Multi-account architecture**: separate environment variables per provider
  - `IMAP_GMAIL_EMAIL` / `IMAP_GMAIL_PASSWORD`
  - `IMAP_INFOMANIAK_EMAIL` / `IMAP_INFOMANIAK_PASSWORD`
  - `IMAP_OUTLOOK_EMAIL` / `IMAP_OUTLOOK_PASSWORD`
  - `IMAP_YAHOO_EMAIL` / `IMAP_YAHOO_PASSWORD`
  - `IMAP_ICLOUD_EMAIL` / `IMAP_ICLOUD_PASSWORD`
  - Custom: `IMAP_CUSTOM_EMAIL`, `IMAP_CUSTOM_PASSWORD`, `IMAP_CUSTOM_SERVER`, `IMAP_CUSTOM_PORT`, `IMAP_CUSTOM_USE_SSL`
- **13 operations**:
  - `connect`: test connection and return account info
  - `list_folders`: list all IMAP folders
  - `search_messages`: search by date, sender, subject, seen/unseen, flagged
  - `get_message`: retrieve full message with body and attachments
  - `download_attachments`: save attachments to files/
  - `mark_read` / `mark_unread`: single message operations
  - `mark_read_batch` / `mark_unread_batch`: bulk operations
  - `move_message` / `move_messages_batch`: move to another folder
  - `mark_spam`: move to spam/junk folder (batch)
  - `delete_message` / `delete_messages_batch`: delete with optional expunge
- **Presets**: automatic server/port/SSL configuration for popular providers
- **Setup time**: 5 minutes (App Password + enable IMAP) vs 30+ minutes for OAuth/GCP
- **MIME parsing**: complete headers, body (text/html), attachments metadata
- **IMAP search**: standard criteria (FROM, SUBJECT, SINCE, UNSEEN, FLAGGED, etc.)
- **Folder normalization**: aliases (`inbox`, `sent`, `trash`, `spam`) mapped to provider-specific names
- **Security**:
  - SSL by default (port 993)
  - Project-chroot for attachments (`files/imap/`)
  - Passwords masked in logs
  - **Zero credentials in tool parameters** (all via `.env` + `provider` selector)
- Architecture: `src/tools/_imap/` (presets, connection, operations, parsers, utils)
- Complete documentation: `src/tools/_imap/README.md` with quick setup guides

#### Git Tool Enhanced
- **New operations**:
  - `fetch`: fetch updates from remote without merging (with `--prune` option)
  - `pull`: fetch + merge or rebase (configurable `rebase`, `ff_only` flags)
  - `rebase`: rebase current branch with `continue`, `abort`, `skip` support
  - `log`: commit history with `max_count`, `one_line`, `graph` options
  - `remote_info`: get remote repository information
- **Conflict detection**: automatic detection for pull/rebase/merge with helpful hints
- **Error handling**: explicit messages for conflicts with resolution commands
- Enable complete git workflow without leaving the tool environment

### 🔄 Changed

#### IMAP multi-account refactor
- Variables d'env séparées par provider (ex: `IMAP_GMAIL_EMAIL`, `IMAP_INFOMANIAK_EMAIL`)
- Paramètre `provider` obligatoire pour sélectionner le compte
- Chaque provider a ses propres credentials isolés
- Architecture modulaire: presets, connection, operations, parsers, utils

#### Documentation updates
- `/README.md`: complete tools catalog (15 tools) with detailed descriptions
- `/src/README.md`: IMAP multi-account env vars and examples
- `/src/tools/README.md`: comprehensive tool guide with architectures
- `/src/tools/_imap/README.md`: detailed IMAP setup and usage guide

#### Git ignore
- Added `files/imap/` to ignore sensitive email data

### 🐛 Fixed
- Git tool now properly handles pull/rebase conflicts with actionable error messages
- IMAP folder normalization works across all providers (Gmail's `[Gmail]/` syntax, etc.)

### 📦 Migration notes
- **IMAP users**: update `.env` with provider-specific variables (see documentation)
- **Git workflows**: `pull`, `fetch`, `rebase` now available directly through the tool
- No breaking changes for existing tools

---

## [1.2.0] - 2025-10-08

### Highlights
- FFmpeg frames: native frame-by-frame detection (PyAV) with moving average + hysteresis + NMS + native refinement
- Much higher recall on compressed cuts (YouTube-like), plus per-frame similarity debug

### Added
- ffmpeg_frames: per-frame debug (t, diff, similarity_pct) and avg_similarity_pct
- ffmpeg_frames: returns exec_time_sec in the API response and in debug.json
- Native video decode dependencies auto-install in scripts/dev.sh (NumPy + PyAV)
- Refactor for maintainability: split FFmpeg tool into `detect.py` (API), `native.py` (PyAV), and `utils.py` (helpers)

### Changed
- ffmpeg_frames sensitivity (defaults): scale=96x96, ma_window=1, threshold_floor=0.05, NMS=0.2s, refine_window=0.5s, min_scene_frames=3
- README mentions native detection and debug fields

### Fixed
- Cases where legacy downsampled CLI missed many hard cuts. Native pass now processes at the video's native FPS

### Migration notes
- Ensure Python 3.11+ and that scripts/dev.sh reinstalls dependencies to get NumPy + PyAV
- If results are still too conservative, consider lowering threshold_floor to 0.04 or min_scene_frames to 2

---

## [1.1.0] - 2025-10-08

### Highlights
- Math tool reliability overhaul: no more generic 500 errors
- New tool: `ffmpeg_frames` (extract frames/images from a video via FFmpeg)
- Dev scripts now load `.env` automatically (Bash + PowerShell)
- Safer repository hygiene: data/runtime folders ignored by default

### Added
- Tool: `ffmpeg_frames` with its canonical spec (`src/tool_specs/ffmpeg_frames.json`)
- App core modules:
  - `src/app_core/safe_json.py` – robust JSON sanitizer/response (handles NaN/Infinity/very large ints safely)
  - `src/app_core/tool_discovery.py` – tool discovery and auto‑reload logic
- Math tool dispatcher (refactor + expansion):
  - New structure:
    - `src/tools/_math/dispatch_core.py` – helpers (error/jsonify/coercions)
    - `src/tools/_math/dispatch_basic.py` – basic ops (arith/trig/complex/log/exp/sqrt) with explicit errors only
    - `src/tools/_math/dispatcher.py` – high‑level router to advanced modules
  - Advanced operations routed to existing modules:
    - Symbolic: `derivative`, `integral`, `simplify`, `expand`, `factor`
    - Calculus: `limit`, `series`, `gradient`, `jacobian`, `hessian`
    - Linear algebra: `mat_add`, `mat_mul`, `mat_det`, `mat_inv`, `mat_transpose`, `mat_rank`, `mat_solve`, `eig`, `vec_add`, `dot`, `cross`, `norm`
    - LA extensions: `pinv`, `cond`, `trace`, `nullspace`, `lu`, `qr`
    - Probability/Stats: `mean`, `median`, `mode`, `stdev`, `variance`, `combination`, `permutation`
    - Distributions: `normal_cdf`, `normal_ppf`, `poisson_pmf`, `poisson_cdf`, `binomial_cdf`, `uniform_pdf`, `uniform_cdf`, `exponential_pdf`, `exponential_cdf`
    - Polynomial: `poly_roots`, `poly_factor`, `poly_expand`
    - Solvers: `solve_eq`, `solve_system`, `nsolve`, `root_find`, `optimize_1d`
    - Number theory: `nth_prime`, `prime_approx`, `is_prime`, `next_prime`, `prev_prime`, `prime_factors`, `factorize`, `euler_phi`, `primes_range`
    - Summations: `sum_finite`, `product_finite`, `sum_infinite`
    - High precision: `eval_precise` (mpmath‑based)

### Changed
- Scripts:
  - `scripts/dev.sh`: now sources `.env` (export), verifies Python 3.11+, creates/activates venv, installs deps + extras (pypdf, sympy, requests), prints config, and launches `python -m server` from `src/`
  - `scripts/dev.ps1`: same parity as Bash (charge `.env`, venv, deps, config, start)
- README updated:
  - Tools list (incl. `ffmpeg_frames`, `script_executor`, `academic_research_super`)
  - Endpoints/config/security sections refreshed

### Fixed
- Math tool returning generic HTTP 500 via API:
  - All error cases now return explicit error objects
- Ensured `.env` is loaded by both the app and the dev scripts

### Repository hygiene
- `.gitignore` now ignores non‑source and local runtime folders:
  - `docs/`, `files/`, `script_executor/` (top‑level), `sqlite3/`, `venv/`, `.venv/`, `.DS_Store`, `__pycache__/`, `*.pyc`
  - Note: source code under `src/tools/_script_executor/` remains tracked

### Migration notes
- Python 3.11+ is now required (enforced by scripts and project metadata)
- Dev scripts source `.env` before installing dependencies and launching the server
- If you kept custom scripts under top‑level `script_executor/`, they're now ignored by Git; move them outside the repo or under a non‑tracked path
- For advanced math features, ensure `sympy` is installed (scripts install it automatically). For high‑precision evaluation, `mpmath` is optional but recommended
