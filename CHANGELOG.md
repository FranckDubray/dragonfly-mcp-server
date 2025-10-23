# Changelog

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
