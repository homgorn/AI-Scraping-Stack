# CONTEXT_MAP.md — Codebase Visual Map

> Machine-readable context for LLMs, IDEs, and agents.
> Read this to understand the full system in one pass.

---

## System Overview

```
USER / AGENT
     │
     ├── index.html          Dashboard UI (vanilla JS, no build)
     │         │
     │         ↓ HTTP REST
     ├── api.py              FastAPI — unified routes (ALL endpoints)
     │         │
     │    ┌────┴────────────────────────────────────────────────┐
     │    ↓                    ↓                                ↓
     │  src/scraper.py      src/llm.py                src/synthesizer.py
     │  ScraperService      LLMRouter                 WebSynthesizer
     │    │                      │                         │
     │    ↓                ┌─────┴──────┐            Multi-agent pipeline:
     │  providers.py  Ollama (local)  OpenRouter (cloud)  Extractor→Ranker→
     │  ProviderRouter    free         300+ models        Researcher→Architect→Coder
     │    │
     │  ┌─┴──────────────────────────────────────────────┐
     │  │ JinaAdapter    (free, no key)                   │
     │  │ ScraplingFast  (local, adaptive)                │
     │  │ Crawl4AI       (local, LLM-ready markdown)      │
     │  │ ScraperAPI     (paid fallback)                  │
     │  │ Scrapingdog    (fastest API)                    │
     │  │ Firecrawl      (best markdown)                  │
     │  │ ZenRows        (balanced price)                 │
     │  │ ScrapeGraphAI  (prompt→JSON)                    │
     │  └─────────────────────────────────────────────────┘
     │
     ├── src/screenshot.py   ScreenshotService + SiteMapService
     │   Crawl4AI → Playwright → Scrapling cascade
     │
     ├── src/vision.py       VisionService + VisualAuditPipeline + ModelRegistry
     │   Ollama VLMs (qwen2.5vl, llava, moondream)
     │   OpenRouter free VLMs (gemma-3n, llama-3.2-vision)
     │
     ├── src/storage.py      SQLite history + JSON model registry
     │
     ├── src/config.py       Pydantic Settings (reads .env)
     │
     ├── src/models.py       All Pydantic schemas
     │
     └── stack.py            Standalone demo + MCP Server
         MCP Tools: scrape_and_analyze_url, quick_extract, stealth_fetch
```

---

## File Responsibilities (strict)

| File | Owns | Must NOT contain |
|------|------|-----------------|
| `src/config.py` | All settings, env vars | Business logic |
| `src/models.py` | All Pydantic schemas | HTTP/IO code |
| `src/llm.py` | LLM calls, prompt building | Scraping code |
| `src/scraper.py` | Fetch orchestration | LLM calls |
| `src/synthesizer.py` | Multi-agent pipeline | Direct DB access |
| `src/storage.py` | SQLite + JSON persistence | HTTP calls |
| `src/screenshot.py` | Screenshot capture + sitemap | LLM calls |
| `src/vision.py` | VLM analysis of images | Scraping code |
| `providers.py` | Provider adapters | FastAPI imports |
| `api.py` | HTTP routes only | Business logic |
| `stack.py` | Standalone demo + MCP | FastAPI imports |
| `index.html` | Dashboard UI | Backend logic |

---

## Data Flows

### 1. Single URL scrape + analyze
```
POST /scrape → api.py
  → ScraperService.scrape(req)
    → ProviderRouter.scrape(url, strategy)
      → JinaAdapter → ScraplingFast → Crawl4AI → ScraperAPI (cascade)
    → returns ScrapeResult
  → LLMRouter.analyze(text, task, complexity)
    → _call_ollama() [low] or _call_openrouter() [medium/high]
  → Storage.save_result()
  → return ScrapeResponse
```

### 2. Synthesis pipeline (N URLs → website)
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

### 3. Screenshot + Visual Audit
```
POST /screenshot/audit → api.py
  → VisualAuditPipeline.run(url, max_pages, tasks)
    → SiteMapService.discover(url) → key pages
    → ScreenshotService.capture_many(pages) → base64 PNGs
    → VisionService.analyze_many(screenshots, task) → VLM insights
    → return { key_pages, pages_analyzed, key_insights }
```

---

## API Endpoints Map

```
GET  /                      → health check
GET  /status                → Ollama + OR + Scrapling status
GET  /config                → current config (keys masked)
PATCH /config               → update config at runtime (persisted to JSON)

POST /scrape                → single URL scrape + LLM analysis
POST /scrape/bulk           → N URLs parallel (semaphore limited)
POST /analyze               → raw text → LLM analysis

POST /synthesize            → N URLs + prompt → website code
POST /synthesize/multi      → N URLs + prompt → multiple variants

POST /screenshot            → capture single URL screenshot
POST /screenshot/bulk       → N screenshots + optional VLM analysis
POST /screenshot/audit      → full visual audit (sitemap→screenshots→VLM)

POST /vision/analyze        → analyze screenshot with VLM
GET  /sitemap               → discover site structure (robots.txt + sitemap)
GET  /vision/models         → list available vision models

GET  /models                → all models (Ollama + OR + custom)
POST /models/ollama/pull    → pull model (SSE stream)
DELETE /models/ollama/{name}
POST /models/openrouter     → add custom OR model
DELETE /models/openrouter/{id}
POST /models/api            → add OpenAI-compatible API
DELETE /models/api/{name}
GET  /models/openrouter/search → search OR catalog

GET  /history               → scrape history (SQLite)
GET  /stats                 → aggregate stats
```

---

## Dependency Order (no circular imports)

```
config → models → llm → scraper → synthesizer → api
                   → storage → api
                   → screenshot → vision → api
providers ← (standalone, no src imports)
stack.py  ← (standalone, no FastAPI imports)
```

---

## Environment Variables

```
OLLAMA_HOST          → src/config.py → LLMRouter._call_ollama()
OLLAMA_MODEL         → src/config.py → LLMRouter default model
OPENROUTER_API_KEY   → src/config.py → LLMRouter._call_openrouter()
OPENROUTER_MODEL     → src/config.py → default cloud model
JINA_API_KEY         → src/config.py → JinaAdapter + trend research
SCRAPERAPI_KEY       → src/config.py → ScraperAPIAdapter
SCRAPINGDOG_KEY      → src/config.py → ScrapingdogAdapter
FIRECRAWL_API_KEY    → src/config.py → FirecrawlAdapter
ZENROWS_KEY          → src/config.py → ZenRowsAdapter
SCRAPINGBEE_KEY      → src/config.py → ScrapingbeeAdapter
SCRAPEDO_KEY         → src/config.py → Scrape.doAdapter
PROXY_URL            → src/config.py → all adapters proxy param
DB_PATH              → src/config.py → Storage SQLite path
```

---

## Key Types

### ScrapeResult (providers.py — dataclass)
```python
url: str
markdown: str    # LLM-ready clean text
text: str        # plain text
html: str        # raw HTML
title: str
links: list[str]
provider: str
tokens_used: int
cost_usd: float
error: str | None
```

### ScrapeResponse (src/models.py — Pydantic)
```python
url, markdown, text, html, title, links, elements, provider,
analysis, model_used, cost_usd, elapsed_ms, error
```

### SynthesisResult (src/synthesizer.py — dataclass)
```python
prompt, urls_processed, code, html, spec, stack,
insights, trends, elapsed_ms, cost_usd, error
```

### ScreenshotResult (src/screenshot.py — dataclass)
```python
url, screenshot_b64, screenshot_path, pdf_b64,
width, height, full_page, provider, elapsed_ms, error
```

### VisionResult (src/vision.py — class)
```python
url, task, analysis, model_used, elapsed_ms, error
```

---

## Vision Tasks

| Task | Output | Best for |
|------|--------|----------|
| `business_intel` | JSON: company, audience, pricing, CTA | Competitor research |
| `design_audit` | Structured: hierarchy, colors, sections | Design inspiration |
| `competitor_analysis` | JSON: USPs, pricing tier, segment | Market analysis |
| `tech_stack` | JSON: framework, UI lib, hosting | Tech research |
| `ux_patterns` | List: nav/hero/CTA patterns | Pattern collection |
| `content_extract` | All visible text by section | Content mining |
| `summary` | 3-5 sentence description | Quick overview |
| `custom` | Pass custom_prompt | Any analysis |

---

## MCP Tools

```bash
scrapling mcp   # built-in Scrapling MCP (6 tools)
python stack.py serve  # extended MCP with Ollama+OpenRouter
```

| Tool | Input | Output |
|------|-------|--------|
| `get` | url | page content |
| `bulk_get` | [urls] | [page contents] |
| `fetch` | url | rendered page |
| `bulk_fetch` | [urls] | [rendered pages] |
| `stealthy_fetch` | url | Cloudflare-bypassed page |
| `bulk_stealthy_fetch` | [urls] | [bypassed pages] |

---

## Skills (automation playbooks)

```
skills/skill_scrape.md      — single URL scraping
skills/skill_synthesize.md  — N URLs → website code
skills/skill_llm.md         — LLM routing + model management
skills/skill_providers.md   — provider selection + cost optimization
skills/skill_screenshot.md  — screenshot + vision analysis
```
