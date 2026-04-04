# USAGE.md — Complete User Guide

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/homgorn/ai-scraping-stack.git && cd ai-scraping-stack

# 2. Install dependencies
pip install -r requirements.txt
scrapling install        # browsers for StealthyFetcher

# 3. Configure
cp .env.example .env
# Open .env, add your keys (minimum — works without them)

# 4. Ollama (local LLM — optional but recommended)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2     # 2GB — base model for analysis

# 5. Check system health
python debug.py --full

# 6. Start the API server
uvicorn api:app --reload --port 8100

# 7. Open the dashboard
open landing.html        # or open in browser
```

---

## Navigation

1. [Configuration](#configuration)
2. [Single URL Scraping](#single-url-scraping)
3. [Bulk Scraping](#bulk-scraping)
4. [Website Synthesis from URLs](#website-synthesis-from-urls)
5. [Screenshots & Visual Analysis](#screenshots--visual-analysis)
6. [Model Management](#model-management)
7. [MCP for AI Agents](#mcp-for-ai-agents)
8. [Python API](#python-api)
9. [Docker](#docker)
10. [Debugging](#debugging)
11. [FAQ](#faq)

---

## Configuration

### Minimal `.env` (works without any keys)

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Recommended `.env`

```env
# Local LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenRouter — 300+ models, free tier available
# Get key: openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-...

# Jina Reader — without key: 20 RPM, with key: 10M free tokens
# Get key: jina.ai
JINA_API_KEY=jina_...
```

### All settings configurable via API (no restart needed)

```bash
curl -X PATCH http://localhost:8100/config \
  -H "Content-Type: application/json" \
  -d '{"openrouter_api_key": "sk-or-v1-..."}'
```

---

## Single URL Scraping

### Via Dashboard (landing.html)

1. Open `landing.html` in your browser
2. Enter the URL
3. Select strategy, task, complexity
4. Click **Analyze**

### Via API

```bash
curl -X POST http://localhost:8100/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "strategy": "smart",
    "task": "summarize",
    "complexity": "low"
  }'
```

### Scrape Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `url` | URL | — | **Required** |
| `strategy` | free / fast / smart / llm / ai / premium / stealth | smart | Provider selection |
| `task` | see below | summarize | What to do with content |
| `complexity` | low / medium / high | low | LLM selection |
| `css_selector` | CSS | "" | Extract specific elements |

### Tasks

| Task | Description |
|------|-------------|
| `summarize` | 3-5 sentence summary |
| `extract_entities` | JSON: people, orgs, prices |
| `classify` | news/product/blog/docs/ecommerce |
| `extract_prices` | JSON: products, prices, availability |
| `sentiment` | JSON: sentiment analysis |
| `extract_links` | JSON: all links |
| `qa:What is the price?` | Question answering |
| `custom:List all emails` | Custom instruction |

### Strategies

| Strategy | Providers | Cost | When to use |
|----------|-----------|------|-------------|
| `free` | Jina → Crawl4AI | $0 | Regular websites |
| `fast` | Scrapling | $0 | Fast, bulk scraping |
| `smart` | Jina → Scrapling → Crawl4AI → ScraperAPI | $0 → $0.0005 | Default, best balance |
| `llm` | Crawl4AI | $0 | Clean markdown for RAG |
| `ai` | ScrapeGraphAI + Ollama | $0 | Prompt → JSON extraction |
| `stealth` | Scrapling StealthyFetcher | $0 | Cloudflare-protected sites |
| `premium` | Firecrawl | ~$0.002 | Best quality markdown |

### Complexity → LLM Selection

```
low    → Ollama llama3.2 (local, free, private)
medium → OpenRouter free tier (Qwen3 30B, Llama 3.3 70B)
high   → OpenRouter configured model (Claude, GPT-4o)
```

---

## Bulk Scraping

```bash
curl -X POST http://localhost:8100/scrape/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://site1.com",
      "https://site2.com",
      "https://site3.com"
    ],
    "strategy": "smart",
    "task": "extract_prices",
    "max_concurrent": 5
  }'
```

Returns: `{ results: [...], total: 3, success: 2, failed: 1 }`

---

## Website Synthesis from URLs

The most powerful feature: feed 1–50 competitor URLs → get a complete website.

### Pipeline

```
Scrape N URLs → Extract patterns → Jina Search trends → Rank insights → Architect → Code
```

### Via API

```bash
curl -X POST http://localhost:8100/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://competitor1.com",
      "https://competitor2.com",
      "https://competitor3.com"
    ],
    "prompt": "Create a SaaS landing page for AI scraping tool. Dark theme, developer audience.",
    "output_format": "html",
    "research_trends": true,
    "complexity": "high"
  }'
```

### Output Formats

| `output_format` | What you get |
|-----------------|-------------|
| `html` | Ready-to-use `<!DOCTYPE html>` file |
| `react` | React component for Vite/CRA |
| `fullstack_spec` | Markdown spec: DB schema, API, docker-compose |

### Multiple Variants

```bash
curl -X POST http://localhost:8100/synthesize/multi \
  -d '{"urls": [...], "prompt": "...", "num_variants": 2}'
# Returns multiple versions (e.g., HTML + React)
```

### Good Prompt Examples

```
"Create a dark-themed SaaS landing page for AI API platform.
Hero: 'Scrape anything, analyze everything'.
Sections: Hero, Features (6), Pricing (3 tiers: Free/$49/$199), API preview, CTA.
Target: developers. Modern, minimal, Tailwind-style."

"Build an e-commerce product page for AI hardware.
Include: specs table, reviews section, comparison chart.
Mobile-first. Conversion-optimized."

"Generate B2B enterprise landing for data analytics SaaS.
Professional tone. Trust signals: logos, numbers, case studies.
CTA: 'Schedule Demo'."
```

---

## Screenshots & Visual Analysis

### Single URL Screenshot

```bash
curl -X POST http://localhost:8100/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "full_page": true, "save": true}'
# Returns: screenshot_b64 (PNG), provider, elapsed_ms
```

### Full Site Audit (Recommended)

```bash
curl -X POST http://localhost:8100/screenshot/audit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://competitor.com",
    "max_pages": 10,
    "tasks": ["business_intel", "design_audit", "competitor_analysis"],
    "save_screenshots": true
  }'
```

**What happens:**
1. Parses `robots.txt` + `sitemap.xml`
2. Discovers key pages (`/about`, `/pricing`, `/features`, ...)
3. Takes screenshots of all pages in parallel (Crawl4AI)
4. VLM analyzes each screenshot

**Returns:**
```json
{
  "key_pages_found": ["/about", "/pricing", "/features"],
  "screenshots_taken": 8,
  "key_insights": {
    "business_intel": [{"url": "...", "analysis": "{company:...}"}],
    "design_audit": [...]
  }
}
```

### Bulk Screenshots + VLM Analysis

```bash
curl -X POST http://localhost:8100/screenshot/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://a.com", "https://b.com", "https://c.com"],
    "tasks": ["business_intel", "tech_stack"],
    "max_concurrent": 3,
    "save": true
  }'
```

### VLM Tasks for Screenshot Analysis

| Task | Returns | Use Case |
|------|---------|----------|
| `business_intel` | JSON: company, audience, pricing | Market research |
| `design_audit` | JSON: layout, colors, quality score | Design analysis |
| `competitor_analysis` | JSON: USPs, segment, strengths | Competitive intelligence |
| `tech_stack` | JSON: framework, CMS, analytics | Technology research |
| `ux_patterns` | JSON: nav, hero, CTA, social proof | Pattern collection |
| `summary` | 3-5 sentence description | Quick overview |
| `custom` | Custom prompt response | Any analysis |

### Manual Screenshot Analysis

```bash
# Step 1: Take screenshot
RESULT=$(curl -s -X POST http://localhost:8100/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}')
B64=$(echo $RESULT | python3 -c "import json,sys; print(json.load(sys.stdin)['screenshot_b64'])")

# Step 2: VLM analysis
curl -X POST http://localhost:8100/vision/analyze \
  -H "Content-Type: application/json" \
  -d "{\"screenshot_b64\": \"$B64\", \"task\": \"competitor_analysis\"}"
```

### Discover Site Structure (robots.txt + sitemap)

```bash
curl "http://localhost:8100/sitemap?url=https://example.com&max_urls=100"
# Returns: sitemap_urls (all pages), key_pages, disallowed
```

---

## Model Management

### Ollama — Local LLM Models (Text)

```bash
ollama pull llama3.2      # 2GB, fast, basic
ollama pull mistral       # 4.1GB, good for extraction
ollama pull qwen2.5       # 4.4GB, multilingual
ollama pull deepseek-r1   # reasoning, complex tasks
```

### Ollama — Vision Models (for Screenshots)

```bash
ollama pull qwen2.5vl:7b  # 4.7GB, best/compact
ollama pull llava:7b      # 4.7GB, reliable classic
ollama pull moondream     # 0.8GB, fast, runs on CPU
```

### List Installed Models

```bash
curl http://localhost:8100/models
```

### Pull New Model (SSE Stream)

```bash
curl -X POST http://localhost:8100/models/ollama/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "mistral"}' --no-buffer
```

### Delete Model

```bash
curl -X DELETE http://localhost:8100/models/ollama/mistral
```

### OpenRouter — Search & Add Models

```bash
# Search free models
curl "http://localhost:8100/models/openrouter/search?free_only=true"

# Add custom model
curl -X POST http://localhost:8100/models/openrouter \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "qwen/qwen3-30b-a3b:free",
    "name": "Qwen3 30B",
    "free": true,
    "tier": "medium"
  }'
```

### Add Custom OpenAI-Compatible API

```bash
# Works with: vLLM, llama.cpp, LM Studio, Groq, Together, Perplexity...
curl -X POST http://localhost:8100/models/api \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Groq",
    "base_url": "https://api.groq.com/openai/v1",
    "api_key": "gsk_...",
    "models": ["llama3-70b-8192", "mixtral-8x7b-32768"],
    "description": "Ultra-fast inference"
  }'
```

---

## MCP for AI Agents

Connect the scraper as a tool to Claude Desktop, Cursor, Windsurf.

### Claude Desktop

Add to `~/.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "ScraplingServer": {
      "command": "scrapling",
      "args": ["mcp"]
    }
  }
}
```

Restart Claude Desktop. 6 tools appear:
- `get` / `bulk_get` — fast fetch
- `fetch` / `bulk_fetch` — with JS rendering
- `stealthy_fetch` / `bulk_stealthy_fetch` — Cloudflare bypass

### Extended MCP (with Ollama + OpenRouter)

```bash
python stack.py serve
```

---

## Python API

### Simple Scraping

```python
import asyncio
from providers import ProviderRouter

async def main():
    router = ProviderRouter({
        "jina_api_key": "jina_...",    # optional
    })

    # Single page
    result = await router.scrape("https://example.com", strategy="smart")
    print(result.markdown)   # LLM-ready text
    print(result.provider)   # which provider handled it
    print(result.cost_usd)   # cost

asyncio.run(main())
```

### LLM Analysis

```python
from src.config import get_settings
from src.llm import LLMRouter

cfg = get_settings()
llm = LLMRouter(cfg)

result = await llm.analyze(
    text="content here",
    task="extract_entities",
    complexity="low",         # low=Ollama, medium=OR free, high=OR paid
)
print(result.analysis)       # analysis result
print(result.model_used)     # "ollama/llama3.2"
print(result.elapsed_ms)     # time in ms
```

### Screenshots & Vision

```python
from src.screenshot import ScreenshotService, SiteMapService
from src.vision import VisionService, ModelRegistry
from src.config import get_settings

cfg = get_settings()
screenshots = ScreenshotService(cfg)
sitemap = SiteMapService(cfg)
registry = ModelRegistry()
vision = VisionService(cfg, registry)

# Discover site structure
site = await sitemap.discover("https://competitor.com")
print(site.key_pages)        # ["/about", "/pricing", ...]
print(len(site.sitemap_urls))  # total pages found

# Screenshot homepage + key pages
shots = await screenshots.capture_many(
    [site.url] + site.key_pages[:9],
    max_concurrent=3,
    output_dir="data/screenshots",
)

# VLM analysis of each screenshot
for shot in shots:
    if shot.screenshot_b64:
        result = await vision.analyze_screenshot(
            shot.screenshot_b64,
            task="competitor_analysis",
            url=shot.url,
        )
        print(f"\n{shot.url}:")
        print(result.analysis)
```

### Website Synthesis

```python
from src.synthesizer import WebSynthesizer
from src.llm import LLMRouter

llm = LLMRouter(cfg)
synth = WebSynthesizer(cfg, llm)

result = await synth.run(
    urls=[
        "https://competitor1.com",
        "https://competitor2.com",
        "https://competitor3.com",
    ],
    prompt="Build SaaS landing page for developer tools. Dark theme.",
    output_format="html",         # html | react | fullstack_spec
    research_trends=True,         # Jina Search for trends
    complexity="high",            # use best LLM
)

# Save the generated site
with open("output_site.html", "w") as f:
    f.write(result.code)

print("Insights:", result.insights[:3])
print("Trends:", result.trends[:3])
print("Elapsed:", result.elapsed_ms, "ms")
```

### History & Statistics

```python
from src.storage import Storage

storage = Storage(cfg)
await storage.init()

# Last 50 scrapes
history = await storage.get_history(limit=50)

# Filter by URL
github = await storage.get_history(url_filter="github.com")

# Session statistics
stats = await storage.get_stats()
print(f"Total: {stats.total_scrapes}, Cost: ${stats.total_cost_usd:.4f}")
```

---

## Docker

### Run Full Stack

```bash
# API + Ollama
docker compose up -d

# View logs
docker compose logs -f api

# Check status
curl http://localhost:8100/status
```

### Pull Models in Docker Ollama

```bash
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull qwen2.5vl:7b
```

### Stop

```bash
docker compose down
```

Data (SQLite, Ollama models) persists via volumes.

---

## Debugging

### Health Check

```bash
# Quick check of all components
python debug.py

# With live scrape test
python debug.py --full

# Show what is broken and how to fix
python debug.py --fix
```

Example output:
```
━━ Config ━━
  ✓ Config loads: .env parsed successfully
  ✓ ollama_host: http://localhost:11434
  ✗ OPENROUTER_API_KEY: not set
    Fix: Add OPENROUTER_API_KEY=sk-or-v1-... to .env

━━ Ollama ━━
  ✓ Ollama server: online at http://localhost:11434
  ✓ model: llama3.2 (2.0 GB)
  ✗ Vision models: not installed
    Fix: ollama pull qwen2.5vl:7b
```

### Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_vision.py -v
pytest tests/test_storage.py -v
pytest tests/test_api.py -v

# With coverage
pytest tests/ --cov=src --cov=providers --cov-report=term-missing
```

### Common Issues

**Ollama not responding**
```bash
ollama serve                    # start manually
curl http://localhost:11434/api/tags   # verify
```

**`ModuleNotFoundError: scrapling`**
```bash
pip install "scrapling[ai,fetchers]"
scrapling install               # install browsers
```

**Crawl4AI browser not found**
```bash
pip install crawl4ai
crawl4ai-setup                  # download Playwright browsers
```

**OpenRouter 401**
```bash
# Verify key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-..."
```

**Screenshot fails**
```bash
# Check Playwright
playwright install chromium
# or Crawl4AI
crawl4ai-setup
```

**`data/` directory not created**
```bash
mkdir -p data
```

---

## FAQ

**Q: Can I scrape without Ollama and OpenRouter?**
A: Yes. Jina Reader works without any keys. Scraping works, AI analysis does not.

**Q: How much does 1000 pages cost?**
A: With `smart` strategy — $0 (Jina + Scrapling). With ScraperAPI fallback — up to $0.49.

**Q: Cloudflare blocking me?**
A: Use `strategy=stealth`. Scrapling StealthyFetcher bypasses CF Turnstile automatically.

**Q: How to get LLM-ready markdown (for RAG)?**
A: `strategy=llm` (Crawl4AI) or `strategy=free` (Jina Reader). Both return clean markdown.

**Q: Synthesis takes too long — how to speed up?**
A: Use `complexity=medium` (OR free instead of Claude). Fewer URLs. Disable `research_trends=false`.

**Q: How to add a new vision model released today?**
A: Add to `src/vision.py` OPENROUTER_FREE_VISION list, or via API if supported.

**Q: How to use as a library (without FastAPI)?**
A: Import directly: `from providers import ProviderRouter`, `from src.vision import VisionService`, etc.

**Q: Where is scrape history stored?**
A: `data/scrapling.db` (SQLite). Access via `GET /history` or Python API.

**Q: How to connect Groq / Together / Perplexity?**
A: `POST /models/api` with `base_url`, `api_key`, `models`. Any OpenAI-compatible API works.
