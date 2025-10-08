

# Tools catalog (src/tools)

This folder contains the MCP tools exposed by the server. Each tool MUST provide:
- A canonical JSON spec file in src/tool_specs/<tool_name>.json (MANDATORY)
- A Python implementation exposing run(...) and spec() (the Python spec() must mirror the JSON)

Source of truth for specs
- The JSON spec in src/tool_specs/<tool_name>.json is the single source of truth for the OpenAI tool schema.
- The Python spec() should typically load and return that JSON file (do not diverge). If they ever differ, JSON wins.
- Validation: arrays MUST define an `items` schema; parameters MUST be an object.

Directory‑first tool layout (small files)
- Prefer a package directory per tool with small, focused modules:

  src/tools/<tool_name>/
    __init__.py        # Thin glue: load spec JSON, expose run()
    api.py             # Input parsing, routing to handlers
    core.py            # Core logic
    validators.py      # Input validation/normalization
    utils.py           # Shared helpers (pure)
    services/          # External I/O (FFmpeg, HTTP, DB), isolated

- Keep modules small and single‑responsibility. Glue in __init__.py should be minimal (no business logic).
- Security: any file access must be chrooted to the project (no absolute/parent paths). Validate user inputs strictly.

Available tools (overview)
- call_llm: 2‑step LLM Orchestrator with tool‑calls then final text answer
- math: numerical + high‑precision + symbolic (see _math/*)
- date: date/time helpers
- git: GitHub API + local Git (restricted)
- gitbook: GitBook helpers
- sqlite_db: SQLite in <project>/sqlite3 chroot
- pdf_search / pdf2text
- reddit_intelligence
- universal_doc_scraper
- script_executor: sandboxed execution of Python scripts orchestrating tools
- academic_research_super
- ffmpeg_frames: extract images/frames with native PyAV shot detection (frame‑by‑frame), debug per‑frame similarity and exec_time_sec
- **imap**: universal IMAP email access (Gmail, Outlook, Yahoo, iCloud, Infomaniak, custom servers) with multi-account support

## IMAP Tool

The IMAP tool provides unified email access across multiple providers with a secure multi-account architecture.

### Security Model
- ✅ **No credentials in tool parameters** — all authentication via `.env` variables
- ✅ **Provider-based configuration** — separate variables per account
- ✅ **Masked passwords** in logs and debug output

### Supported Providers
- **gmail**: Google Mail (requires App Password if 2FA enabled)
- **outlook**: Microsoft Outlook/Office365
- **yahoo**: Yahoo Mail
- **icloud**: Apple iCloud Mail
- **infomaniak**: Swiss hosting provider (mail.infomaniak.com)
- **custom**: Generic IMAP server (requires IMAP_SERVER, IMAP_PORT, IMAP_USE_SSL)

### Configuration (.env)
```bash
# Gmail account
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=your_app_password

# Infomaniak account
IMAP_INFOMANIAK_EMAIL=contact@yourdomain.com
IMAP_INFOMANIAK_PASSWORD=your_password

# Outlook account
IMAP_OUTLOOK_EMAIL=user@outlook.com
IMAP_OUTLOOK_PASSWORD=your_password

# Custom server
IMAP_EMAIL=user@example.com
IMAP_PASSWORD=password
IMAP_SERVER=mail.example.com
IMAP_PORT=993
IMAP_USE_SSL=true
```

### Operations
- **connect**: Test connection and return account info
- **list_folders**: List all available IMAP folders
- **search_messages**: Search emails by criteria (date, sender, subject, seen/unseen, flagged, etc.)
- **get_message**: Retrieve full message with body and attachments metadata
- **download_attachments**: Download attachments from a message
- **mark_read** / **mark_unread**: Mark single message
- **mark_read_batch** / **mark_unread_batch**: Bulk mark operations
- **move_message** / **move_messages_batch**: Move to another folder
- **mark_spam**: Move to spam/junk folder
- **delete_message** / **delete_messages_batch**: Delete messages (with optional expunge)

### Example Usage
```python
# List unread emails (Infomaniak)
{
  "tool": "imap",
  "params": {
    "provider": "infomaniak",
    "operation": "search_messages",
    "folder": "inbox",
    "query": {"unseen": true},
    "max_results": 20
  }
}

# Mark emails as read (Gmail)
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "mark_read_batch",
    "folder": "inbox",
    "message_ids": ["123", "456", "789"]
  }
}

# Move to spam (Outlook)
{
  "tool": "imap",
  "params": {
    "provider": "outlook",
    "operation": "mark_spam",
    "folder": "inbox",
    "message_id": "42"
  }
}
```

### Architecture
```
src/tools/_imap/
  __init__.py     # Package marker
  presets.py      # Provider configurations (servers, ports, folders)
  connection.py   # IMAP connection management
  operations.py   # Core operations (search, mark, move, delete)
  parsers.py      # Email parsing (headers, body, attachments)
  utils.py        # Utilities (date conversion, folder mapping)
  README.md       # Detailed tool documentation
```

Spec JSON location and naming
- Location: src/tool_specs/<tool_name>.json
- The `function.name` must match the Python tool package/module name exposed by the server.
- Example Python adapter to load JSON spec:

  def spec():
      import json, os
      here = os.path.dirname(__file__)
      spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', '<tool_name>.json'))
      with open(spec_path, 'r', encoding='utf-8') as f:
          return json.load(f)

Adding a new tool (required steps)
1) Create src/tools/<tool_name>/ as a package with __init__.py exposing run() and spec().
2) Add src/tool_specs/<tool_name>.json (MANDATORY) describing the OpenAI function schema.
3) Implement small modules under src/tools/<tool_name>/ (api.py, core.py, validators.py, utils.py, services/*).
4) Enforce security (sandbox, path validations) and explicit errors (no generic 500s).
5) Start the server and GET /tools to see the tool registered.

Notes
- Tests and examples are recommended but kept outside the repo's ignored data paths (e.g., not under docs/ unless explicitly whitelisted).
- Do not commit user data or runtime outputs; use chrooted, ignored folders.

 
