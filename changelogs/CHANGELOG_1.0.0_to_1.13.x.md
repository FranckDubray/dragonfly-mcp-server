# Changelog (Archive) — v1.0.0 → v1.13.x

Note: This file restores the early history before the simplified CHANGELOG.

---

## [1.13.0]
- docs: add excel_to_sqlite tool documentation (v1.13.0)

## [1.12.x]
- feat: add ollama_local tool - comprehensive Ollama interface

## [1.11.0]
- feat(v1.11.0): office_to_pdf tool - Word/PowerPoint to PDF conversion

## [1.10.0]
- feat(v1.10.0): email_send tool + youtube_search/video_transcribe improvements

## [1.9.x]
- Add generate_edit_image tool for AI-powered image editing
- feat: Add ship_tracker tool with real-time AIS data via AISStream.io WebSocket
- feat(ship_tracker): integrate real aisstream.io WebSocket API
- feat(tools): add ship_tracker tool with AIS data
- docs: remove redundant ENV_VARIABLES.md
- docs: add YOUTUBE_API_KEY documentation to ENV_VARIABLES.md
- docs: update documentation for youtube_search tool
- feat(tools): add youtube_search tool with YouTube Data API v3
- feat(ui): add alphabetical sorting for tools in control panel
- feat(aviation_weather): add upper air weather tool with Open-Meteo API

## [1.0.0] - Initial release
- FastAPI server with MCP tools discovery
- Auto-reload tools from src/tools/
- Safe JSON serialization (NaN, Infinity, bigints)
- Panneau de contrôle web
- Configuration via .env

Tools (14)
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
