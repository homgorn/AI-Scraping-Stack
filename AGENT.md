# AGENT.md — AI Agent Context File
> Read this file FIRST before touching any code.
> Designed for Claude, GPT-4, Cursor, Aider, Copilot.

---

## What This Project Is

**AI Scraping Stack** — 6-layer intelligent web intelligence platform.

```
Layer 6: MCP Server        → scrapling mcp (tools for AI agents)
Layer 5: Dashboard UI      → index.html (vanilla JS, no build)
Layer 4: API Gateway       → api.py (FastAPI, ALL routes unified)
Layer 3: Intelligence      → LLM Router + Vision (VLM analysis)
Layer 2: Synthesis Engine  → Multi-agent: N URLs → website code
Layer 1: Provider Router   → 10+ scraping providers, cascade fallback
```

**Core value:** Input competitor URLs → get screenshots, business analysis, design audit, and generated website code — all free.

---

## Full File Map

```
src/config.py           ← READ FIRST. Pydantic Settings, all env vars
src/models.py           ← ALL Pydantic schemas live here only
src/llm.py              → LLMRouter: Ollama + OpenRouter calls
src/scraper.py          → ScraperService: fetch orchestration
src/synthesizer.py      → WebSynthesizer: multi-agent N URLs → website
src/storage.py          → SQLite history + JSON model registry
src/screenshot.py       → ScreenshotService + SiteMapService
src/vision.py           → VisionService + VisualAuditPipeline + ModelRegistry
src/sitemap.py          → re-export of SiteMapService
src/__init__.py

providers.py            → ProviderRouter + 8 adapter classes
api.py                  → FastAPI routes (ALL endpoints unified)
stack.py                → Standalone demo + FastMCP extended server
landing.html            → SEO-optimized frontend (main UI)
index.html              → Redirect to landing.html

skills/skill_scrape.md      → how to scrape single URL
skills/skill_synthesize.md  → how to run N URLs → website pipeline
skills/skill_llm.md         → LLM routing, model management
skills/skill_providers.md   → provider selection, cost optimization
skills/skill_screenshot.md  → screenshot + vision analysis

CONTEXT_MAP.md          → visual system map, data flows, API map
ROADMAP.md              → what's done, what's planned, tech debt
AGENT.md                → this file
CHAT_HISTORY.md         → session log

.env.example            → all env vars with comments
requirements.txt        → Python dependencies
USAGE.md                → user documentation
debug.py                → health check + diagnostics

tests/test_api.py       → integration tests (FastAPI TestClient)
tests/test_providers.py → provider unit tests
tests/test_storage.py   → storage unit tests
tests/test_screenshot.py→ screenshot unit tests
tests/test_vision.py    → vision unit tests
conftest.py             → shared test fixtures

DEPLOY_RAILWAY.md       → deploy backend to Railway
DEPLOY_TIMEWEB.md       → deploy to Timeweb Cloud (with GPU)
DEPLOY_SHARED_HOSTING.md→ deploy frontend to shared hosting

.github/workflows/ci.yml→ GitHub Actions CI (lint + test + build)
Dockerfile              → Docker image
docker-compose.yml      → API + Ollama
Makefile                → dev commands
pyproject.toml          → Python packaging
.gitignore              → git ignore rules
```

.env.example            → all env vars with comments
requirements.txt        → Python dependencies
USAGE.md                → user documentation
debug.py                → health check + diagnostics
```

---

## Architecture Rules (enforce strictly)

1. **`api.py` is THIN** — only HTTP routing. No business logic. Always delegates to `src/`.
2. **`src/config.py` only** — never `os.getenv()` outside this file.
3. **`src/models.py` only** — never define Pydantic models in `api.py`.
4. **`providers.py` is standalone** — no `src/` imports, usable without FastAPI.
5. **No circular imports** — order: `config → models → llm/scraper/storage → synthesizer → api`
6. **Two `ScrapeResult` types exist** — `providers.py` has a dataclass (internal), `src/models.py` has Pydantic (API/DB). ScraperService converts between them.
7. **All routes in `api.py`** — no separate route files. Everything unified.

---

## Key Patterns

### LLM complexity routing
```python
# low   → Ollama local (free, private)
# medium → OpenRouter free tier (Qwen3, Llama3.3)
# high  → OpenRouter configured model (Claude, GPT-4o)
result = await llm_router.analyze(text, task="summarize", complexity="low")
```

### Provider cascade (strategy="smart")
```
1. Jina Reader (free, no key, clean markdown)
2. Scrapling fast (local, adaptive selectors)
3. Crawl4AI (local, LLM-ready markdown)
4. ScraperAPI (paid fallback)
```

### Synthesis pipeline
```
scrape_all(urls) → extract_all() → research_trends() → rank() → architect() → code()
```
All agents call `LLMRouter.analyze()` with `complexity="high"` by default.

### Screenshot cascade
```
Crawl4AI (screenshot=True) → Playwright → Scrapling DynamicFetcher
```

### Vision cascade (all FREE)
```
Ollama: qwen2.5vl:7b → llava:7b → moondream  (local, private)
OR:     gemma-3n-e4b-it:free → llama-3.2-11b-vision:free  (cloud)
```

---

## Common Tasks for Agent

### Add a scraping provider
1. Add class in `providers.py` (copy JinaAdapter pattern)
2. Add instance to `ProviderRouter.__init__`
3. Add to `_build_chain` for relevant strategies
4. Add env var in `src/config.py`
5. Add to `.env.example`
6. Update `skills/skill_providers.md` table

### Add a new endpoint
1. Schema in `src/models.py`
2. Logic in `src/llm.py` or `src/scraper.py` or new `src/X.py`
3. Thin route in `api.py`: validate → call service → return

### Add a new LLM task
1. Add to `TASK_PROMPTS` dict in `src/llm.py`
2. Add to task `<select>` in `index.html`
3. Document in `skills/skill_llm.md`

### Add a new vision task
1. Add to `VISION_TASKS` dict in `src/vision.py`
2. Document in `skills/skill_screenshot.md`

### Wire storage to a route
```python
from src.storage import Storage
storage = Storage(get_settings())
await storage.init()
await storage.save_result(result)
```

---

## Known Tech Debt (fix in priority order)

1. ~~HIGH — Closure bug in `providers.py._build_chain`~~ ✅ FIXED (default arg pattern)
2. **MEDIUM** — No httpx connection pooling — `AsyncClient` created per request in `llm.py` + `providers.py`
3. **MEDIUM** — No integration tests for scrape/synthesize endpoints (only validation tests)
4. **LOW** — CORS `allow_origins=["*"]` — restrict in prod
5. **LOW** — Root-level `vision.py` removed ✅
6. **LOW** — `api_vision.py` removed ✅ (routes merged into `api.py`)

---

## Testing

```bash
pytest tests/ -v                          # all tests
pytest tests/test_llm.py -v               # LLM only
pytest tests/ --cov=src --cov=providers   # coverage

# Important: clear settings cache in tests
from src.config import get_settings
get_settings.cache_clear()
```

---

## Running

```bash
# Dev server
uvicorn api:app --reload --port 8100

# MCP server
scrapling mcp              # built-in Scrapling MCP
python stack.py serve      # extended MCP with Ollama+OpenRouter

# Demo
python stack.py            # standalone demo

# Docker
docker-compose up          # API + Ollama
```
