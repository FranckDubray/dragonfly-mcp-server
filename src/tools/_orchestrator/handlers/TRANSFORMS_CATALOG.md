# Orchestrator Transforms Catalog

This document lists the available transform handlers exposed by the orchestrator so LLM prompts and process graphs can reference them consistently.

Each entry provides: kind, purpose, main inputs/outputs, and a minimal node example.

Note: Handlers are auto-registered via Python packages under:
- src/tools/_orchestrator/handlers/transforms/ (core, general-purpose)
- src/tools/_orchestrator/handlers/transforms_domain/ (domain-specific)

---

## Core transforms (generic)

### kind: set_value
- Purpose: pass-through any JSON-serializable value.
- Inputs: value: any
- Outputs: result: any
- Example:
```json
{"type":"transform","handler":"set_value","inputs":{"value":42},"outputs":{"result":"ctx.answer"}}
```

### kind: add
- Purpose: numeric addition.
- Inputs: a, b (numbers)
- Outputs: result (number)

### kind: increment
- Purpose: increase a value by step.
- Inputs: value, step=1
- Outputs: result

### kind: decrement
- Purpose: decrease a value by step.
- Inputs: value, step=1
- Outputs: result

### kind: multiply
- Purpose: numeric multiplication.
- Inputs: a, b
- Outputs: result

---

## JSON transforms

### kind: json_ops
- Purpose: parametric JSON operations: get, pick, set, rename, remove, merge.
- Inputs (per op):
  - op: "get" | "pick" | "set" | "rename" | "remove" | "merge"
  - data, path/default (get), pick (list), set_values (dict), rename (dict), remove (list), merge (dict)
- Outputs: varies; for get => result

### kind: normalize_llm_output
- Purpose: robustly parse LLM outputs into valid JSON (tolerates code fences, partial JSON, escapes).
- Inputs: content (string/JSON), fallback_value (optional)
- Outputs: parsed (JSON)

---

## Array/list transforms

### kind: array_concat
- Purpose: concatenate multiple lists into a flat list.
- Inputs: lists: array of lists
- Outputs: items: list

### kind: array_ops
- Purpose: parametric list ops: filter, unique_by, sort_by, map, take, skip.
- Inputs: op, items, predicate | key/order | fields | count
- Outputs: items and optional metrics (kept/dropped)

### kind: dedupe_by_url
- Purpose: remove duplicates by URL (keep_first or replace).
- Inputs: items (list of dict), url_key="url"
- Outputs: items, removed, kept

---

## Date/time & numbers

### kind: date_ops
- Purpose: format/add/diff on ISO dates or epoch seconds.
- Inputs: ops: [{op:"format"|"add"|"diff", ...}]
- Outputs: per op (save_as or result)

### kind: coerce_number
- Purpose: coerce arbitrary input to float (supports fractions, percentages).
- Inputs: value, default=0.0, allow_percent=false
- Outputs: number

---

## Text & templating

### kind: format_template
- Purpose: format a string with {{key}} placeholders.
- Inputs: template, context
- Outputs: result (string)

### kind: sanitize_text
- Purpose: remove HTML, normalize whitespace, truncate.
- Inputs: text, max_length, remove_html, normalize_whitespace
- Outputs: text, truncated, lengths

---

## Validation & utilities

### kind: idempotency_guard
- Purpose: check if an action_id was already completed.
- Inputs: action_id, completed_actions[]
- Outputs: skip (bool), action_id

### kind: filter_multi_by_date
- Purpose: filter multiple named lists by date >= cutoff in a single pass.
- Inputs: cutoff_iso, items_map{name->list}, date_paths{name->path}, unix_seconds{name->bool}
- Outputs: {name}_items_recent, {name}_kept, {name}_dropped

---

## Domain-specific (AI curation)

These are frequently used across curation/ETL flows:
- normalize_llm_output (see above)
- array_ops/concat (see above)
- json_ops (see above)
- dedupe_by_url (see above)

---

## Domain-specific (Minecraft chess)

### kind: normalize_entities
- Purpose: normalize Minecraft entities for chess usage (name cleanup, piece_key, color/letter, square_tag, pos, uuid, tags).
- Inputs: items (from list_entities), piece_tag_map (optional)
- Outputs: items (normalized)
- Example:
```json
{"type":"transform","handler":"normalize_entities","inputs":{"items":"${cycle.mc.raw}"},"outputs":{"items":"${cycle.mc.norm}"}}
```

### kind: pos_to_square
- Purpose: project entity positions to chessboard squares using origin/axis/case_size/epsilon.
- Inputs: items, origin{x,y,z}, axis, case_size, epsilon
- Outputs: items (with square), map (piece_key->square), invalid (list)

### kind: compare_positions
- Purpose: detect unique move from prev->curr maps.
- Inputs: prev (map), curr (map)
- Outputs: unique(bool), piece_key, from, to, changed_count

### kind: uci_build
- Purpose: build UCI string from from/to with simple pawn promotion.
- Inputs: from/from_, to, piece_letter
- Outputs: uci

---

## Minimal patterns (recipes)

- Dedupe by best candidate per key:
  1) array_ops sort_by key="pos.y" order="desc"
  2) array_ops op=unique_by key="piece_key"

- Robust LLM JSON:
  - normalize_llm_output content="${llm.content}" → parsed

- JSON field extraction:
  - json_ops op="get" data="${obj}" path="a.b[0].c" → result

---

## Notes
- All handlers are pure transforms (no external I/O), suitable for graph nodes of type "transform".
- For I/O (HTTP, DB, MC commands), use io nodes with handler http_tool or the dedicated tool.
- New domain transforms should be added under transforms_domain/ and imported in __init__.py to auto-register.
