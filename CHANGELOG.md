# Changelog

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
