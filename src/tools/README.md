# Tools catalog (src/tools)

This folder contains the MCP tools exposed by the server. Each tool provides:
- run(...) implementation (business logic)
- spec() returning the OpenAI tool/function schema (or a matching JSON spec in src/tool_specs)

Available tools
- call_llm
  - Purpose: 2-step LLM Orchestrator with tool-calls then final text answer
  - Notes: enforces tool usage (first call: tool_choice=required or explicit function; second call: tool_choice=none, no tools in payload). SSE streaming lines must start with "data: ".
  - Env: AI_PORTAL_TOKEN, LLM_ENDPOINT, optional LLM_DEBUG
  - Internals: see _call_llm/core.py, _call_llm/tool_execution.py, _call_llm/streaming.py, _call_llm/mcp_tools.py

- math
  - Purpose: numerical + high-precision + symbolic math
  - Modules: see _math/* (advanced, arithmetic, calculus, complex_ops, expression_parser, high_precision, linear_algebra, linear_algebra_ext, number_theory, output_format, polynomial, probability, probability_ext, solvers, stats_ext, summation, symbolic)
  - Notes: precision>16 requires mpmath; if missing, returns a clear error (no silent fallback)

- date
  - Purpose: date/time operations: now/today, add, diff, format, parse, weekday, week_number

- git
  - Purpose: GitHub API + local Git operations (restricted to project root)
  - Env: GITHUB_TOKEN
  - Security: local ops chrooted; limited set of allowed actions

- gitbook
  - Purpose: GitBook discovery/content/sitemap helpers

- sqlite_db
  - Purpose: SQLite operations in a safe chroot under <project>/sqlite3
  - Security: database names strictly validated (no absolute paths, no ../)

- pdf_search
  - Purpose: keyword search inside PDFs

- pdf2text
  - Purpose: text extraction from PDF

- reddit_intelligence
  - Purpose: multi search, experts, trends, sentiment

- script_executor
  - Purpose: run controlled scripts via a sandboxed helper (see _script/*)
  - Security: strict checks before execution

- universal_doc_scraper
  - Purpose: universal document detector + scraper

- academic_research_super
  - Purpose: aggregator for advanced research workflows

Specifications
- JSON specs are kept in src/tool_specs/*.json (matching tool names). Arrays MUST define an `items` schema to pass OpenAI validation.

Add a new tool (quick guide)
1) Create src/tools/<tool_name>.py with run() and spec()
2) Optionally add src/tool_specs/<tool_name>.json overriding/aligning the Python spec()
3) Keep security in mind (chroot for any file access; forbid absolute/parent paths)
4) Start the server and check GET /tools to see the tool registered
