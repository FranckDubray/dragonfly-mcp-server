# Changelog

## [1.54.1] - 2025-10-22

### 🛠 Fixes & Improvements (Image & 3D Import)
- fix(image): no more holes — RGBA images are flattened on white; any accidental "air" mapping is replaced by a safe white block (white_concrete or white_wool).
- feat(palette): exclude gravity-affected blocks (e.g., sand, gravel, concrete_powder) from color mapping to avoid falling blocks in builds.
- feat(image): default palette is enforced to "both" in code (wool + concrete) when none specified; `wool_only` still supported (deprecated) and mapped.
- feat(voxel): improved color extraction for 3D model import — priority: vertex colors → face colors → texture sampling via UV; reliable fallback if none present.
- compatibility: no breaking changes; tool spec unchanged.

## [1.54.0] - 2025-10-22

### ✨ NEW: Image Rendering for Minecraft Control
- render_image operation (docs/images → blocks) with two modes:
  - mode: wall (vertical) or floor (horizontal)
  - target_width with aspect-ratio preserved (NEAREST)
- Color mapping & quality:
  - palette: wool | concrete | both (default: both)
  - distance: rgb (fast) | lab (perceptual)
  - dither: Floyd–Steinberg option (reduces banding)
- Path handling: robust resolution (relative, prefixed, absolute under /docs/images), debug fields (resolved_path, searched_paths on error)
- Options: clear_area, image_mapping=color|single, block_type for single

### 🧪 Compatibility & Defaults
- wool_only still supported (deprecated) → internally mapped to palette
- Default palette now “both” (wool + concrete) for higher contrast

### 🧱 Palette
- Extended high-contrast palette: full 16 wool + 16 concrete colors (+ neutrals)

### 🧭 Positioning
- FIX: floor mode now respects params.position.y exactly (no fallback to y=64)

### 🧩 Refactor
- Split render_image into modules (< 7KB each):
  - operations/image/api.py (orchestrator)
  - operations/image/paths.py (path resolution)
  - operations/image/palette_quant.py (palette & quantization)
  - operations/image/placer.py (placement & command gen)

### 📦 Dependencies
- Add pillow>=10.0.0 (required for image loading)

### 🧾 Spec update
- src/tool_specs/minecraft_control.json: add render_image, palette/distance/dither fields

## [1.53.0] - 2025-10-22

### ✨ NEW: Minecraft Control Tool
- **Nouveau tool**: `minecraft_control` pour contrôle serveur Minecraft via RCON (localhost)
- **8 opérations**:
  - `execute_command`: commandes Minecraft brutes
  - `spawn_entities`: spawn entités avec patterns (line/circle/grid/random)
  - `build_structure`: structures géométriques (cube/sphere/pyramid/cylinder/wall/platform)
  - `import_3d_model`: import modèles 3D voxlisés (FBX/OBJ/STL/GLB/GLTF)
  - `control_player`: téléportation, rotation caméra, gamemode
  - `set_environment`: météo, temps jour/nuit, difficulté
  - `batch_commands`: exécution batch avec throttling
  - `get_player_state`: récupération position/rotation joueur
- **Fonctionnalités avancées**:
  - Positionnement relatif au joueur (forward/up/right offsets)
  - Auto-chunking structures >32k blocs (limite Minecraft /fill)
  - Voxelisation modèles 3D avec mapping couleur → blocs MC (palette 35 blocs)
  - Patterns spawn: line, circle, grid, random avec spacing configurable
  - Formes géométriques: sphere, pyramid, cylinder (approximation voxel)
  - NBT tags support pour customisation entités
  - Throttling batch (50ms delay par défaut)
  - Truncation warnings (limite 50 items output)
- **Architecture**:
  - Client RCON: wrapper `mcipc` avec retry (3x) et pool connexions
  - Geometry engine: calculs 3D (rotation yaw/pitch, patterns, shapes)
  - Voxel engine: `trimesh` loader + voxelizer + block mapper (color matching)
  - Utils: validators, command builder, chunker, NBT builder
  - Config hardcoded (localhost:25575, no auth)
- **Dépendances**: `mcipc>=2.4.0`, `trimesh[easy]>=4.0.0`, `numpy>=1.24.0`
- **Conformité LLM_DEV_GUIDE**: fichiers <7KB, specs JSON canoniques, truncation warnings, logging, error handling
- **README**: docs complètes avec exemples conversationnels (25 fichiers, ~2500 lignes)

Note: Nécessite serveur Minecraft avec `enable-rcon=true` dans `server.properties`.

## [1.52.0] - 2025-10-21

### ✨ NEW: Excel Row
- **Nouveau tool**: `excel_row` pour manipuler les lignes Excel avec formats avancés
- **Opérations**: insert_row, update_row, delete_row, list_backups, restore_backup
- **Formats Excel**:
  - Number formats: date_iso, date_short_fr, currency_eur_fr, currency_usd_en, accounting_eur_fr, percent_0/2, decimal_2/3, integer, custom
  - Font: name, size (6-72), bold, italic, underline, color
  - Alignment: horizontal/vertical, wrap_text, indent
  - Background color + border (thin/medium/thick)
- **Granularité**: row_format (défaut) + columns_format (overrides par colonne)
- **Parsing dates**: parse.date_input_format (auto/DD/MM/YYYY/YYYY-MM-DD/MM/DD/YYYY) séparé de l'affichage Excel
- **Backups**: création, listing, restauration (docs/office/excel_backups/)
- **Mapping**: clés normalisées ou noms Excel originaux acceptés
- **Support**: colonnes > 26 (A-Z-AA-AZ...)
- **Compatibilité**: params legacy (color, border_color, date_format) mappés automatiquement

Note: Warning Excel "contenu illisible" peut apparaître avec formats complexes (bénin, formats appliqués correctement).

## [1.51.2] - 2025-10-20

### ♻️ Refactor & Stability
- refactor(engine): split orchestrator_core into logical modules (<7KB each)
  - core_nodes_common.py (begin/exec start/end, scope resets)
  - core_nodes_handler.py (IO/transform execution, retries, mapping, debug)
  - core_nodes_decision.py (decisions, debug)
- fix(engine): remove engine/__init__ import side-effects to eliminate circular imports
- chore(start): purge all debug.* flags at start unless debug.enable_on_start=true
- runner: bootstrap hardened (worker_name/db_file injected)

No breaking changes. Improves debuggability and respects file-size guard.

## [1.51.1] - 2025-10-20

### 🛠 Maintenance & Hotfixes
- feat(transforms): add domain transforms `array_ops`, `date_ops`, `json_ops`, and `array_concat`; auto-register on bootstrap
- refactor(utils): centralize error handling (ErrorHandler, safe_extract), validators, file utils
- chore(db): remove legacy files (db_manager.py, query_executor.py), consolidate db_facade.py
- fix(process): handle empty Mermaid gracefully (return stub graph)
- docs(process): update README with complete architecture, endpoints, transforms catalog

## [1.51.0] - 2025-10-19

### 🎯 Process Overlay Enhancements
- feat(overlay): KPIs dernière heure (steps, IO, errors, avg duration)
- feat(overlay): replay controls (⏮⏪⏹⏩⏭) with autoplay + follow-tail
- feat(overlay): horloge "temps machine" (current step timestamp)
- feat(overlay): triple highlight trail (current + 2 previous nodes)
- feat(overlay): détection incohérence logs ↔ graph (alertes détaillées)
- refactor(overlay): split JS modules (state, data, render, UI core/side/highlight/replay, consistency)
- fix(process): throttling render Mermaid (1/s anti-flood)
- perf(overlay): préchargement Mermaid au show (cache)

## [1.50.0] - 2025-10-18

### 🔧 Workers Architecture Overhaul
- refactor(workers): modular config builder (core, tools, instructions, voice, session)
- feat(config): dynamic instructions (worker_query schema, process graph, runtime stats)
- feat(tools): worker_query tool proxy with error handling
- feat(scanner): auto-discovery sqlite3/worker_*.db + metadata extraction
- fix(realtime): hybrid config (DB-first, fallback .env)
- docs(workers): complete README with architecture flows

Older entries archived in `changelogs/`.
