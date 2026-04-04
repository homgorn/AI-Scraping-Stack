# ROADMAP.md

> AI Scraping Stack — Development Roadmap

---

## Status Legend
- ✅ Done
- 🔄 In progress / partial
- 📋 Planned
- 💡 Ideas / future

---

## v0.1 — Foundation ✅

- ✅ 4-layer architecture: Scrapling → Ollama → MCP → OpenRouter
- ✅ FastAPI REST backend (`api.py`)
- ✅ Dashboard UI (`index.html`) — dark terminal aesthetic
- ✅ Scrapling v0.4 integration (fast/stealth/dynamic modes)
- ✅ Ollama local LLM (llama3.2/mistral/qwen)
- ✅ OpenRouter SDK (300+ models, free tier routing)
- ✅ MCP server (scrapling mcp — 6 tools for Claude Desktop/Cursor)
- ✅ Bulk scraping with semaphore concurrency control

---

## v0.2 — Architecture cleanup ✅

- ✅ `src/config.py` — Pydantic Settings (replaces global dict)
- ✅ `src/models.py` — centralized Pydantic schemas
- ✅ `src/llm.py` — LLM routing service (SRP)
- ✅ `src/scraper.py` — scraping service (SRP)
- ✅ `src/storage.py` — SQLite history + JSON model registry
- ✅ `providers.py` — unified adapter: 8 providers, ProviderRouter
- ✅ `requirements.txt` — Python dependencies
- ✅ `.env.example` — all env vars with comments
- ✅ `stack.py` — standalone demo + MCP server
- ✅ Tests: `test_llm.py`, `test_providers.py`
- ✅ All routes unified in `api.py`
- ✅ `/history` and `/stats` endpoints wired to Storage
- ✅ `/analyze` endpoint for raw text analysis
- 📋 Fix: closure bug in `providers.py` `_build_chain` lambdas
- 📋 httpx connection pooling

---

## v0.3 — Synthesis Engine ✅

- ✅ `src/synthesizer.py` — multi-agent pipeline
- ✅ `POST /synthesize` — N URLs + prompt → website code
- ✅ `POST /synthesize/multi` — returns multiple variants
- ✅ Agent pipeline: Extractor → Ranker → Researcher → Architect → Coder
- ✅ Jina Search integration for trend research
- ✅ Output formats: HTML / React / Full-stack spec
- ✅ Skills docs: `skills/skill_synthesize.md`
- 📋 Add synthesis tab to `index.html` dashboard
- 📋 Stream synthesis progress via SSE
- 📋 Save synthesis results to SQLite

---

## v0.3.1 — Visual Intelligence Layer ✅

- ✅ `src/screenshot.py` — ScreenshotService (Crawl4AI→Playwright→Scrapling cascade)
- ✅ `src/vision.py` — VisionService + VisualAuditPipeline + ModelRegistry
- ✅ `src/sitemap.py` — robots.txt + sitemap.xml discovery
- ✅ `POST /screenshot` — single URL screenshot
- ✅ `POST /screenshot/bulk` — N screenshots + VLM analysis
- ✅ `POST /screenshot/audit` — full visual audit pipeline
- ✅ `POST /vision/analyze` — analyze screenshot with VLM
- ✅ `GET /sitemap` — discover site structure
- ✅ `GET /vision/models` — list available VLMs
- ✅ `skills/skill_screenshot.md` — full playbook

### Free VLM models
- **Local**: qwen2.5vl:7b, llava:7b, moondream (Ollama)
- **Cloud**: gemma-3n-e4b-it:free, llama-3.2-11b-vision:free (OpenRouter)

### Vision tasks
- business_intel, design_audit, competitor_analysis
- tech_stack, ux_patterns, content_extract, summary, custom

### Next for this module
- 📋 Dashboard tab: "Visual Audit" with screenshot preview
- 📋 Screenshot diff: compare same URL over time
- 📋 Batch export: ZIP of all screenshots
- 📋 Vision → synthesis integration: screenshots feed into WebSynthesizer
- 📋 PDF export: full-page PDF (Crawl4AI pdf=True already works)

---

## v0.4 — SEO Landing + Deploy ✅

- ✅ `landing.html` — SEO-оптимизированный фронтенд (Schema.org, FAQ, Open Graph)
- ✅ 5 вкладок: Scrape, Synthesize, Screenshot, Audit, Vision
- ✅ Статический HTML — размещается на любом shared hosting
- ✅ Связь с бэкендом через `API_URL` (fetch)
- ✅ `DEPLOY_RAILWAY.md` — инструкция деплоя бэкенда на Railway
- ✅ `DEPLOY_TIMEWEB.md` — инструкция деплоя на Timeweb Cloud (с GPU/Ollama)
- ✅ `DEPLOY_SHARED_HOSTING.md` — инструкция деплоя фронтенда на виртуальный хостинг
- ✅ Nginx конфиг для проксирования `/api/` → бэкенд
- ✅ systemd сервис для автозапуска API
- ✅ Dockerfile + docker-compose.yml
- ✅ .gitignore
- ✅ Makefile
- ✅ pyproject.toml
- 📋 Production CORS: restrict from `*` to configured origins
- 📋 Rate limiting on API endpoints
- 📋 API key authentication for frontend

---

## v0.5 — Dashboard: Full UI 📋

- 📋 Synthesis tab: URL input, prompt, format selector, live progress
- 📋 Visual Audit tab: sitemap explorer, screenshot gallery, VLM insights
- 📋 History tab: past scrapes + syntheses, re-run, export
- 📋 Code preview with syntax highlight (Prism.js CDN)
- 📋 Download button → saves .html / .jsx / .md file

---

## v0.5 — Storage & History 🔄

- ✅ Wire `Storage` into scrape routes
- ✅ `GET /history` with filtering
- ✅ `GET /stats` — aggregate statistics
- 📋 History panel in dashboard
- 📋 Export history: CSV / JSON download
- 📋 Deduplication: skip re-scraping same URL if cached < N hours
- 📋 Save synthesis results to SQLite

---

## v0.6 — Scheduler 📋

- 📋 `POST /schedule` — cron scraping jobs
- 📋 APScheduler integration
- 📋 Webhook notifications
- 📋 Schedule management in dashboard

---

## v0.7 — RAG Pipeline 📋

- 📋 `POST /rag/index` — scrape → chunk → embed → store
- 📋 `POST /rag/query` — semantic search
- 📋 `POST /rag/chat` — chat with indexed websites
- 📋 Dashboard: "Knowledge Base" tab

---

## v0.8 — Agent Enhancements 📋

- 📋 Iterative synthesis: agent reviews code, improves in 3 rounds
- 📋 Competitor analysis agent
- 📋 SEO analysis agent
- 📋 Price monitoring agent
- 📋 Content gap analysis

---

## v0.9 — Production Hardening 📋

- 📋 Rate limiting (slowapi)
- 📋 API key authentication
- 📋 CORS: restrict from `*`
- 📋 Structured logging
- 📋 Prometheus metrics
- 📋 httpx connection pooling
- 📋 Graceful shutdown

---

## v1.0 — Public Release 💡

- 💡 OpenAPI docs polished
- 💡 CLI: `scrapling scrape <url>` / `scrapling synthesize <urls> "<prompt>"`
- 💡 PyPI package
- 💡 Docker Hub image
- 💡 One-click deploy button
- 💡 GitHub Actions CI/CD

---

## Tech Debt Tracker

| Issue | File | Priority |
|-------|------|----------|
| Closure bug in `_build_chain` lambdas | providers.py | High |
| httpx client per-request (no pooling) | providers.py, llm.py | Medium |
| Root-level vision.py duplicate | vision.py | Low |
| CORS `allow_origins=["*"]` | api.py | Low |
| No integration tests | tests/ | Medium |

---

## Contributing

1. Fork → feature branch → PR
2. `pytest tests/` must pass before PR
3. New providers → `providers.py` + skill doc in `skills/`
4. New endpoints → schema in `src/models.py` first, route in `api.py` last
5. Update `CONTEXT_MAP.md` when adding files
