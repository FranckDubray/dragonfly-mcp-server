# 🔧 Orchestrator — Generic JSON-driven FSM

**Production-ready orchestrator for long-running, stateful workflows.**

---

## 🎯 Overview

The **orchestrator** is a generic, JSON-driven Finite State Machine (FSM) engine that executes process graphs with **zero business logic in the engine**. It's designed for:

- 🔄 **Long-running workflows** (email triage, data pipelines, monitoring)
- 🧠 **Stateful automation** (context persistence across cycles)
- 🔗 **MCP tool orchestration** (call any MCP tool: imap, call_llm, sqlite, etc.)
- 🛡️ **Robust execution** (retry policies, error handling, cooperative cancel)
- 🔥 **Hot-reload** (update process at runtime without restart)

---

## 🚀 Quick Start

### 1. Create a process file

`workers/hello_world.process.json`:

```json
{
  "version": "1.0",
  "worker_ctx": {
    "sleep_seconds": 10
  },
  "graph": {
    "nodes": [
      {"name": "START", "type": "start"},
      {
        "name": "log_hello",
        "type": "transform",
        "handler": "sleep",
        "inputs": {"seconds": 0},
        "outputs": {"slept": "cycle.result.done"}
      },
      {"name": "END", "type": "end"}
    ],
    "edges": [
      {"from": "START", "to": "log_hello"},
      {"from": "log_hello", "to": "END"}
    ]
  }
}
```

### 2. Start the worker

```python
from src.tools.orchestrator import run

# Start
result = run(
    operation="start",
    worker_name="hello_world",
    worker_file="workers/hello_world.process.json"
)
print(result)
# → {"accepted": true, "status": "starting", "pid": 12345, ...}
```

### 3. Check status

```python
status = run(operation="status", worker_name="hello_world")
print(status)
# → {"status": "sleeping", "heartbeat": "2025-01-18 17:45:00.123456", ...}
```

### 4. Stop the worker

```python
stop = run(operation="stop", worker_name="hello_world", stop={"mode": "soft"})
print(stop)
# → {"accepted": true, "status": "ok", "message": "Cancel flag set", ...}
```

---

## 📂 Process File Structure

### Minimal Process

```json
{
  "version": "1.0",
  "worker_ctx": {
    "timezone": "UTC",
    "sleep_seconds": 60
  },
  "graph": {
    "nodes": [
      {"name": "START", "type": "start"},
      {"name": "END", "type": "end"}
    ],
    "edges": [
      {"from": "START", "to": "END"}
    ]
  }
}
```

### Full Process (with all features)

```json
{
  "version": "1.0",
  "process_version": "1.2.0",
  "metadata": {
    "description": "Email triage workflow",
    "author": "ops-team"
  },
  "worker_ctx": {
    "timezone": "UTC",
    "sleep_seconds": 300,
    "llm_model": "gpt-4o-mini",
    "retry_defaults": {"max": 2, "delay_sec": 1}
  },
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "scopes": [
    {
      "name": "mbox",
      "reset_on": ["START"],
      "seed": {"folder": "INBOX"}
    }
  ],
  "graph_mermaid": "graph TD\n  START-->fetch_emails\n  ..."
}
```

---

## 🔧 Node Types

### START (entry point)

```json
{"name": "START", "type": "start"}
```

### END (exit point, reboucle to START)

```json
{"name": "END", "type": "end"}
```

### IO (call MCP tool)

```json
{
  "name": "fetch_emails",
  "type": "io",
  "handler": "http_tool",
  "inputs": {
    "tool": "imap",
    "operation": "search_messages",
    "provider": "gmail",
    "folder": "INBOX",
    "query": {"unseen": true}
  },
  "outputs": {
    "messages": "cycle.mbox.messages"
  },
  "retry": {"max": 2, "delay_sec": 60},
  "timeout_sec": 120
}
```

### Transform (internal handler, pure function)

```json
{
  "name": "wait_5s",
  "type": "transform",
  "handler": "sleep",
  "inputs": {"seconds": 5},
  "outputs": {"slept": "cycle.metrics.slept"}
}
```

### Decision (conditional routing)

#### Decision: truthy

```json
{
  "name": "check_messages",
  "type": "decision",
  "decision": {
    "kind": "truthy",
    "input": "${cycle.mbox.messages}"
  }
}
```

Edges:
```json
{"from": "check_messages", "to": "process", "when": "true"},
{"from": "check_messages", "to": "END", "when": "false"}
```

#### Decision: enum_from_field

```json
{
  "name": "classify",
  "type": "decision",
  "decision": {
    "kind": "enum_from_field",
    "input": "${cycle.msg.classification}",
    "normalize": "upper",
    "fallback": "default"
  }
}
```

Edges:
```json
{"from": "classify", "to": "handle_spam", "when": "SPAM"},
{"from": "classify", "to": "handle_ham", "when": "HAM"},
{"from": "classify", "to": "handle_unsure", "when": "default"}
```

---

## 🧩 Context Model

### worker_ctx (read-only constants)

```json
"worker_ctx": {
  "timezone": "UTC",
  "llm_model": "gpt-4o-mini",
  "sleep_seconds": 300
}
```

Access: `${worker.llm_model}`

### cycle_ctx (stateful, read/write)

Namespaced by user-defined scopes:

```json
"scopes": [
  {"name": "mbox", "reset_on": ["START"], "seed": {"folder": "INBOX"}},
  {"name": "msg", "reset_on": ["enter_loop"], "seed": {}},
  {"name": "report", "reset_on": ["START"], "seed": {}}
]
```

Access: `${cycle.mbox.folder}`, `${cycle.msg.uid}`

Write: `"outputs": {"uid": "cycle.msg.uid"}`

---

## 🔄 Handlers

### Built-in handlers

| Handler | Type | Description |
|---------|------|-------------|
| `sleep` | Transform | Cooperative sleep (checks cancel every 0.5s) |
| `http_tool` | IO | Generic MCP tool caller (POST /execute) |

### Using http_tool (call any MCP tool)

```json
{
  "name": "call_llm_classify",
  "type": "io",
  "handler": "http_tool",
  "inputs": {
    "tool": "call_llm",
    "operation": "call",
    "model": "${worker.llm_model}",
    "messages": [
      {"role": "system", "content": "Classify email as SPAM or HAM"},
      {"role": "user", "content": "${cycle.msg.text}"}
    ]
  },
  "outputs": {
    "content": "cycle.msg.classification"
  },
  "retry": {"max": 2, "delay_sec": 60},
  "timeout_sec": 180
}
```

**⚠️ Important**: When using `call_llm`, map `"content"` specifically (not the full response object).

---

## 🔁 Retry Policies

### Node-level retry

```json
{
  "name": "fetch_data",
  "type": "io",
  "handler": "http_tool",
  "inputs": {...},
  "retry": {
    "max": 3,
    "delay_sec": 2
  }
}
```

**Behavior:**
- Total attempts = max + 1 (initial + retries)
- Exponential backoff: `delay_sec * 2^(attempt-1)`
- Example: max=3, delay=2 → 4 attempts with 2s, 4s, 8s delays
- Respects `Retry-After` header (e.g., 429 rate limit)

---

## 🛡️ Error Handling

### HandlerError structure

```python
class HandlerError(Exception):
    message: str       # max 400 chars
    code: str          # e.g., "TIMEOUT", "HTTP_429"
    category: str      # "io" | "validation" | "permission" | "timeout"
    retryable: bool    # True if retry may succeed
    details: dict      # optional (e.g., {"retry_after_sec": 60})
```

### 3-level retry strategy

1. **Transport retry** (automatic, 3×)
   - Network failures, DNS errors, connection timeouts
   - Exponential backoff: 0.5s, 1s, 2s

2. **HTTP status normalization**
   - 429 Rate Limit → retryable with Retry-After
   - 4xx Client → non-retryable
   - 5xx Server → retryable

3. **Node retry policy**
   - Configured per node (max, delay_sec)
   - Applied only if error.retryable=True

---

## 📊 Logging & Observability

### DB: sqlite3/worker_<name>.db

#### Table: job_state_kv

Global state (phase, heartbeat, pid, cancel flag, etc.)

```sql
SELECT * FROM job_state_kv WHERE worker='my_worker';
```

#### Table: job_steps

Per-node execution logs:

```sql
SELECT node, status, started_at, finished_at, duration_ms, edge_taken
FROM job_steps
WHERE worker='my_worker' AND cycle_id='cycle_001'
ORDER BY id;
```

Columns:
- `node` — node name
- `status` — 'running', 'succeeded', 'failed', 'skipped'
- `handler_kind` — handler used (e.g., 'http_tool', 'sleep')
- `edge_taken` — decision route (e.g., 'true', 'SPAM')
- `details_json` — compact JSON (inputs, outputs, errors, attempts)

---

## 🔒 Security

### Chroot enforcement

- ✅ Process files **must** be under `workers/` directory
- ❌ Rejects `..`, absolute paths, escaping symlinks

### Secrets

- ⚠️ Do NOT put secrets in `worker_ctx` (logged in DB)
- ✅ Use environment variables or external secret store
- ✅ Pass secrets via MCP tool params (not logged)

---

## 🧪 Testing

### Production Tests (Validated ✅)

#### Test 1: Smart Daily Insight Generator
**File**: `workers/test_smart_insight.process.json`

**Features tested**:
- ✅ Multiple `call_llm` calls (classification + context-aware generation)
- ✅ Decision `enum_from_field` (MORNING|AFTERNOON|EVENING routing)
- ✅ Decision `truthy` (quality validation)
- ✅ Complex context resolution (nested objects in prompts)
- ✅ Scopes lifecycle (data, analysis, result)
- ✅ Retry policies on LLM calls
- ✅ 6 MCP tools orchestrated (date, device_location, open_meteo, astronomy, call_llm×2)

**Results**:
- ✅ 11 nodes executed successfully
- ✅ 2.4s total cycle time
- ✅ Correct routing (EVENING → evening_insight)
- ✅ Quality validation passed
- ✅ 0 errors, 0 retries needed

---

## 📚 Examples

See `workers/` directory for example processes:

- `test_minimal.process.json` — START → END (minimal)
- `test_advanced.process.json` — decision + sleep + retry
- `test_mcp_tool.process.json` — MCP tool call (date)
- `test_smart_insight.process.json` — ⭐ **Full LLM workflow** (classification + routing + generation)
- `production_briefing.process.json` — Daily briefing (3 tools orchestrated)

---

## 🔧 Troubleshooting

### Worker not starting

```bash
# Check logs
tail -f logs/orchestrator_*.log

# Check DB state
sqlite3 sqlite3/worker_<name>.db "SELECT * FROM job_state_kv;"
```

### Stuck in 'starting' phase

- Check if runner process is alive: `ps aux | grep runner`
- Check heartbeat: `SELECT heartbeat FROM job_state_kv WHERE worker='<name>';`
- If stale (> 90s), kill process and restart

### Process errors

```sql
-- Check failed steps
SELECT node, details_json
FROM job_steps
WHERE worker='<name>' AND status='failed'
ORDER BY id DESC
LIMIT 10;
```

### call_llm output mapping

⚠️ **Common mistake**: Mapping entire response instead of `content` field.

**Wrong**:
```json
"outputs": {
  "classification": "cycle.analysis.result"  ❌
}
```

**Correct**:
```json
"outputs": {
  "content": "cycle.analysis.result"  ✅
}
```

The `call_llm` tool returns `{"result": {"content": "...", "usage": {...}}}`. The `http_tool` handler extracts `result`, giving you `{"content": "...", "usage": {...}}`. Map `"content"` specifically to get the string value.

---

## 📖 Architecture Docs (membank)

Full technical specs in membank:

1. `orchestrator_tool_design.md` — tool API, states, operations
2. `orchestrator_process_schema.md` — JSON format spec
3. `orchestrator_contexts.md` — context resolution/mapping
4. `orchestrator_logging.md` — DB schema, logging
5. `orchestrator_decisions.md` — decision kinds registry
6. `orchestrator_handlers.md` — handler interface, MCP client
7. `orchestrator_runner.md` — detached runner, signals
8. `orchestrator_mcp_error_handling.md` — 3-level retry, errors
9. `orchestrator_implementation.md` — implementation summary
10. `n8n_make_diff.md` — comparison with n8n/Make

---

## 🎯 Roadmap

### v1.0 (current) ✅
- [x] Tool controller (start/stop/status)
- [x] Runner detached (signals, cancel)
- [x] Engine graph execution
- [x] Context resolution (recursive)
- [x] Handlers (sleep, http_tool)
- [x] Decisions (truthy, enum_from_field)
- [x] Retry policies (expo backoff)
- [x] Logging (job_steps)
- [x] Chroot security
- [x] Production tests (call_llm workflows)

### v1.1 (next)
- [ ] Scope lifecycle hooks (enter/leave triggers)
- [ ] Hot-reload at runtime (process_uid check)
- [ ] Inspector tool (query logs, visualize graph)
- [ ] Circuit breaker (fail-fast after N failures)
- [ ] Transform handlers (sanitize_text, normalize_llm_output)

### v2.0 (future)
- [ ] Distributed execution (multi-worker coordination)
- [ ] Webhooks (trigger cycles on external events)
- [ ] Metrics export (Prometheus/StatsD)
- [ ] Web UI (graph editor, live monitoring)

---

## 🤝 Contributing

1. Keep files < 7KB (split if needed)
2. No business logic in engine (handlers only)
3. Add tests for new features
4. Update membank docs

---

## 📄 License

MIT (same as dragonfly-mcp-server)

---

**Questions? Check membank docs or open an issue!** 🚀
