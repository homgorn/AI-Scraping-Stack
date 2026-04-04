# Changelog

All notable changes to AI Scraping Stack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 12 Wiki pages (EN + RU) in `docs/wiki/`
- `CHANGELOG.md`
- `robots.txt` and `sitemap.xml` for SEO
- `LICENSE` (MIT)
- `SECURITY.md` for vulnerability disclosure
- `CODE_OF_CONDUCT.md`
- `.dockerignore` and `.editorconfig`
- `scripts/setup.py` for automatic `.env` creation
- Graceful shutdown in `api.py`
- Pagination in `/history` endpoint
- Analytics placeholder in landing pages
- Pre-commit hook configuration

### Fixed
- Removed hardcoded API_KEY from landing pages
- Fixed closure bug in `providers.py` `_build_chain`
- Fixed `stack.py` top-level imports (try/except)
- Fixed `debug.py` imports (removed `hf_token`, `custom_models_path`)
- Fixed `conftest.py` Settings (removed deprecated fields)
- Moved all test files to `tests/` directory
- Removed duplicate `vision.py` and `api_vision.py` from root
- Cleaned up temp directories and zip archives

### Changed
- `index.html` now redirects to `landing.html`
- `README.md` restructured with English as primary
- `USAGE.md` fully translated to English, Russian moved to `USAGE_RU.md`
- `ROADMAP.md` fully English, Russian version added
- Updated `AGENT.md` with complete file map
- Updated `CONTEXT_MAP.md` with new modules

### Security
- Added API Key middleware to `api.py`
- Added Rate Limiter (10 req/min per IP)
- Added Global Exception Handler (no stack trace leaks)
- Added Security Headers (TrustedHostMiddleware)

---

## [0.4.0] — 2026-04-04

### Added
- SEO-optimized landing pages (EN + RU) with JSON-LD schema
- Full `src/` module structure (config, models, llm, scraper, storage, vision, screenshot, synthesizer)
- Unified FastAPI with all routes (scrape, synthesize, screenshot, vision, models, history, stats)
- Provider Router with 8 adapters and cascade fallback
- Multi-agent synthesis pipeline
- Visual audit pipeline (sitemap → screenshots → VLM analysis)
- MCP Server integration
- Docker + docker-compose
- GitHub Actions CI + Keep-Alive workflow
- Deploy guides: Railway, Timeweb, Shared Hosting
- 5 Skill files for automation playbooks

### Initial Release
- 6-layer architecture
- 10+ scraping providers
- Zero-cost mode (Jina + Ollama + OpenRouter free tier)
