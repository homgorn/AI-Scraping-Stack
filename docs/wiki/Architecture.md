# Architecture

> Understanding the 6-layer system design, data flows, and module responsibilities.

## System Overview

AI Scraping Stack is built on a **6-layer architecture** where each layer has a single responsibility and communicates through well-defined interfaces.

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 6: MCP Server                                   │
│  "scrapling mcp" — 6 tools for Claude Desktop / Cursor  │
├─────────────────────────────────────────────────────────┤
│  LAYER 5: Dashboard UI                                 │
│  landing.html — SEO-optimized, bilingual, responsive    │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: API Gateway (FastAPI)                        │
│  api.py — ALL routes unified, middleware, security      │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: Intelligence Engine                          │
│  src/llm.py   → LLM Router (Ollama + OpenRouter)       │
│  src/vision.py → VisionService + VLM analysis           │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Synthesis Engine                             │
│  src/synthesizer.py — Multi-agent: N URLs → website     │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Provider Router                              │
│  providers.py — 10+ adapters, cascade fallback          │
└─────────────────────────────────────────────────────────┘
```

## Module Map

```
scrapling/
├── src/                          # Business logic modules
│   ├── config.py                 # Pydantic Settings (all env vars)
│   ├── models.py                 # All Pydantic schemas
│   ├── llm.py                    # LLMRouter: Ollama + OpenRouter
│   ├── scraper.py                # ScraperService: orchestration
│   ├── storage.py                # SQLite history + JSON registry
│   ├── screenshot.py             # ScreenshotService + SiteMapService
│   ├── vision.py                 # VisionService + VisualAuditPipeline
│   ├── synthesizer.py            # WebSynthesizer: multi-agent pipeline
│   └── sitemap.py                # Re-export of SiteMapService
├── api.py                        # FastAPI engine (all routes)
├── providers.py                  # ProviderRouter + 8 adapters
├── stack.py                      # MCP Server + standalone demo
├── landing.html                  # SEO frontend (EN)
├── landing_ru.html               # SEO frontend (RU)
├── render.yaml                   # Render.com Blueprint
├── requirements.txt              # Dependencies
└── .github/workflows/            # CI/CD + Keep-Alive
```

## Data Flows

### Flow 1: Single URL Scrape + Analyze

```
POST /scrape → api.py
  → ScraperService.scrape(req)
    → ProviderRouter.scrape(url, strategy)
      → JinaAdapter → ScraplingFast → Crawl4AI → ScraperAPI (cascade)
    → returns ScrapeResult
  → LLMRouter.analyze(text, task, complexity)
    → _call_ollama() [low] or _call_openrouter() [medium/high]
  → Storage.save_result()
  → return ScrapeResponse (JSON)
```

### Flow 2: Synthesis Pipeline (N URLs → Website)

```
POST /synthesize → api.py
  → WebSynthesizer.run(urls, prompt, format)
    → _scrape_all(urls) [parallel, ≤5 concurrent]
    → _extract_all(contents) [Extractor agent x N]
    → _research_trends(topic) [Jina Search x 2]
    → _rank_insights(extractions) [Ranker agent]
    → _architect(prompt, insights, trends) [Architect agent]
    → _generate_code(spec, format) [Coder agent]
    → return { code, insights, trends, spec, stack }
```

### Flow 3: Screenshot + Visual Audit

```
POST /screenshot/audit → api.py
  → VisualAuditPipeline.run(url, max_pages, tasks)
    → SiteMapService.discover(url) → key pages
    → ScreenshotService.capture_many(pages) → base64 PNGs
    → VisionService.analyze_many(screenshots, task) → VLM insights
    → return { key_pages, pages_analyzed, key_insights }
```

## Dependency Order (No Circular Imports)

```
config → models → llm → scraper → synthesizer → api
                   → storage → api
                   → screenshot → vision → api
providers ← standalone (no src imports)
stack.py  ← standalone (no FastAPI imports)
```

## Security Middleware

All POST/PUT/DELETE requests pass through `security_middleware` in `api.py`:

1. **Rate Limiting** — Max 10 requests/minute per IP (in-memory sliding window)
2. **API Key Check** — If `API_KEY` env var is set, requires `X-API-Key` header
3. **CORS** — Configurable origins (default: `*` for dev)

## Provider Cascade

| Strategy | Providers | Cost | Use Case |
|----------|-----------|------|----------|
| `free` | Jina → Crawl4AI | $0 | Regular websites |
| `fast` | Scrapling | $0 | Fast, bulk scraping |
| `smart` | Jina → Scrapling → Crawl4AI → ScraperAPI | $0 → $0.0005 | Default, best balance |
| `llm` | Crawl4AI | $0 | Clean markdown for RAG |
| `ai` | ScrapeGraphAI + Ollama | $0 | Prompt → JSON extraction |
| `stealth` | Scrapling StealthyFetcher | $0 | Cloudflare-protected sites |
| `premium` | Firecrawl | ~$0.002 | Best quality markdown |

## LLM Routing

| Complexity | Model | Cost | Speed |
|------------|-------|------|-------|
| `low` | Ollama (llama3.2) | Free | Fast (local) |
| `medium` | OpenRouter free (Qwen3 30B) | Free | Medium |
| `high` | OpenRouter configured (Claude, GPT-4o) | Paid | Medium |

## Storage

| Component | Type | Purpose |
|-----------|------|---------|
| `data/scrapling.db` | SQLite | Scrape history, stats |
| `data/models.json` | JSON | Custom model registry |
| `data/screenshots/` | Files | Captured screenshots |

## High-Load Upgrades

For production with heavy traffic:

| Component | Standard | High-Load |
|-----------|----------|-----------|
| Database | SQLite | PostgreSQL + PgBouncer |
| Cache | In-memory | Redis |
| Server | Uvicorn | Gunicorn + Uvicorn workers |
| Queue | asyncio.Semaphore | Celery + RabbitMQ |
| Monitoring | Logs | Prometheus + Grafana |
| Tracing | None | OpenTelemetry |
