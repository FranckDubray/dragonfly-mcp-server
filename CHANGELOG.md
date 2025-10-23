# Changelog

## 1.6.0 — 2025-10-23

Improvements (Minecraft Control / list_entities)
- Robust SNBT parsing and automatic fallback:
  - When full SNBT is not available or braces are unbalanced, the tool now switches to per-field queries (Pos, Rotation, CustomName, id, Tags, Dimension, UUID) and reassembles entities by index.
  - Quote-aware multi-compound extraction supports concatenated outputs like "<name> has the following entity data: {…}" repeated on one line.
- Output fidelity: raw output returned verbatim.
  - New field result.raw contains the full, unmodified server output (no client-side truncation or ellipsis).
  - Removed result.raw_lines (no longer needed).
- Custom name normalization:
  - result.entities[*].custom_name is now normalized (outer quotes removed), e.g. '"wP_a2"' -> 'wP_a2'.
- Optional fields:
  - result.entities[*].type (from NBT id without namespace, e.g. "cat").
  - result.entities[*].uuid when available.
- Module split (<7KB per file) for maintainability:
  - operations/list_entities/api.py — orchestration and response shaping.
  - operations/list_entities/fallback.py — per-field query path and utility splitting.
  - operations/list_entities/fields.py — field decoders and counted fallback extraction.

Notes
- Sorting by distance requires a known center. If a full selector is supplied and relative_to_player=false, center is None and distance sort is a no-op. Provide area.center or rely on relative_to_player=true without a prebuilt selector for distance sorting.

Migration
- No breaking changes to tool spec. Consumers may now rely on result.raw for debugging and on normalized custom_name for grouping.

## 1.55.7 — 2025-10-23

Fixes / Chore
- Dev scripts: remove absolute paths, use only relative paths in scripts/dev.sh and scripts/dev.ps1 (GitHub-friendly, portable).
- Tool spec: vscode_control category fixed to `developer_tools` (LLM dev guide compliance).
- Tool spec: orchestrator displayName updated to `Call LLM`.

## 1.55.6 — 2025-10-23

Chore
- Dependencies updated in pyproject.toml:
  - Added: skyfield

## 1.55.5 — 2025-10-23

Chore
- Dependencies updated in pyproject.toml:
  - Added: yt_dlp, beautifulsoup4 (bs4), websocket-client (websocket), fastapi, uvicorn
- Version bump to 1.55.5

## 1.55.3 — 2025-10-23

Improvements
- Decisions: clearer errors with operand values and types
  - `compare` now reports both operands and their Python types when numeric operators are used on non-numeric values.
  - `enum_from_field` error includes original value + type before normalization.
- Failure logs enriched with IO context
  - On step failure, we now include a debug preview of resolved inputs for io/transform and resolved decision spec + input for decisions.
- Status: remove misleading last_error
  - `status` no longer exposes `last_error` (stale). Errors should be read from `job_steps` (failed steps) and `crash_logs`.
  - `start` clears `last_error` to avoid stale error carry-over between runs.

## 1.55.2 — 2025-10-23

New
- VS Code Control tool added
  - New MCP tool `vscode_control` with operations to open files/folders, diff, manage extensions, settings, search workspace, and preview/apply file changes.

## 1.55.1 — 2025-10-23

Improvements
- Orchestrator Engine: reliable failure logging
  - Per-node exceptions now write a step with status="failed" (job_steps) and a crash entry (crash_logs) with normalized details. Debug pauses are not treated as failures.
- Configurable cycle length ceiling
  - Default max nodes per cycle raised to 1000 and can be configured via env var `ORCHESTRATOR_MAX_NODES_PER_CYCLE`.
- Subgraphs: recursive flattening
  - `flatten_subgraphs` now flattens nested subgraphs recursively before merging into the main graph.
- Validation hardening
  - Reject graphs with more than one `when='always'` edge from the same source node.
- Transforms
  - `format_template`: missing keys now preserve the original `{{placeholder}}` instead of producing unexpected output.
- Housekeeping
  - `debug_utils` switched to clean relative import for `utcnow_str`.

Notes
- Backward compatible. No changes required for existing process files. To change the node traversal ceiling per cycle, set `ORCHESTRATOR_MAX_NODES_PER_CYCLE` in your environment.
