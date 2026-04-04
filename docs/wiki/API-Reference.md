# API Reference

> Complete reference for all REST endpoints, parameters, and response formats.

**Base URL:** `http://localhost:8100` (local) or your deployed URL.

## Authentication

If `API_KEY` is set in environment variables, all POST/PUT/DELETE requests require:
```
X-API-Key: your-secret-key
```

GET endpoints (health, status, models) are always public.

---

## Core Endpoints

### GET `/` — Health Check

Returns service status and version.

```bash
curl http://localhost:8100/
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### GET `/status` — Service Status

Returns detailed status of all components.

```bash
curl http://localhost:8100/status
```

**Response:**
```json
{
  "timestamp": "2026-04-04T12:00:00",
  "ollama": {"online": true, "models_count": 3, "host": "http://localhost:11434"},
  "openrouter": {"configured": true},
  "scrapling": {"installed": true, "version": "0.4.0"},
  "custom_apis": 0,
  "custom_models": 0
}
```

### GET `/config` — Current Config

Returns current configuration (API keys masked).

```bash
curl http://localhost:8100/config
```

### PATCH `/config` — Update Config

Update configuration at runtime (persisted to JSON).

```bash
curl -X PATCH http://localhost:8100/config \
  -H "Content-Type: application/json" \
  -d '{"max_concurrent": 10}'
```

---

## Scraping Endpoints

### POST `/scrape` — Single URL

Scrape one URL with optional LLM analysis.

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

**Parameters:**

| Parameter | Type | Values | Default | Required |
|-----------|------|--------|---------|----------|
| `url` | string | URL | — | ✅ |
| `strategy` | string | free/fast/smart/llm/ai/premium/stealth | smart | ❌ |
| `task` | string | summarize/extract_entities/classify/extract_prices/sentiment | summarize | ❌ |
| `complexity` | string | low/medium/high | low | ❌ |
| `css_selector` | string | CSS selector | "" | ❌ |

**Response:**
```json
{
  "url": "https://example.com",
  "markdown": "# Example Domain\n\nThis domain is for use in...",
  "text": "Example Domain This domain is for...",
  "title": "Example Domain",
  "provider": "jina",
  "analysis": "This is a placeholder website...",
  "model_used": "ollama/llama3.2",
  "cost_usd": 0.0,
  "elapsed_ms": 1250
}
```

### POST `/scrape/bulk` — Multiple URLs

Scrape up to 50 URLs in parallel.

```bash
curl -X POST http://localhost:8100/scrape/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://site1.com", "https://site2.com"],
    "strategy": "smart",
    "task": "summarize",
    "max_concurrent": 5
  }'
```

**Response:**
```json
{
  "results": [...],
  "total": 2,
  "success": 2
}
```

### POST `/analyze` — Raw Text Analysis

Analyze raw text with LLM (no scraping).

```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long text to analyze...",
    "task": "extract_entities",
    "complexity": "medium"
  }'
```

---

## Synthesis Endpoints

### POST `/synthesize` — Generate Website

Generate a website from competitor URLs.

```bash
curl -X POST http://localhost:8100/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://competitor1.com", "https://competitor2.com"],
    "prompt": "Create a SaaS landing page. Dark theme.",
    "output_format": "html",
    "research_trends": true,
    "complexity": "high"
  }'
```

**Parameters:**

| Parameter | Type | Values | Default | Required |
|-----------|------|--------|---------|----------|
| `urls` | string[] | URLs | — | ✅ |
| `prompt` | string | Description | — | ✅ |
| `output_format` | string | html/react/fullstack_spec | html | ❌ |
| `research_trends` | boolean | true/false | true | ❌ |
| `complexity` | string | low/medium/high | high | ❌ |

### POST `/synthesize/multi` — Multiple Variants

Generate multiple website variants.

```bash
curl -X POST http://localhost:8100/synthesize/multi \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://competitor1.com"],
    "prompt": "Create a landing page",
    "num_variants": 2
  }'
```

---

## Screenshot & Vision Endpoints

### POST `/screenshot` — Capture Screenshot

```bash
curl -X POST http://localhost:8100/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "width": 1440,
    "full_page": true,
    "save": false,
    "pdf": false
  }'
```

### POST `/screenshot/bulk` — Bulk Screenshots

Capture screenshots for multiple URLs with optional VLM analysis.

```bash
curl -X POST http://localhost:8100/screenshot/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://a.com", "https://b.com"],
    "tasks": ["business_intel", "design_audit"],
    "max_concurrent": 3,
    "save": true
  }'
```

### POST `/screenshot/audit` — Full Visual Audit

Discover sitemap → screenshot all pages → VLM analysis.

```bash
curl -X POST http://localhost:8100/screenshot/audit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://competitor.com",
    "max_pages": 10,
    "tasks": ["business_intel", "design_audit"],
    "save_screenshots": true
  }'
```

### POST `/vision/analyze` — Analyze Screenshot

Analyze a screenshot with VLM.

```bash
curl -X POST http://localhost:8100/vision/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "screenshot_b64": "iVBORw0KGgo...",
    "task": "business_intel",
    "url": "https://example.com"
  }'
```

**Vision Tasks:**

| Task | Description |
|------|-------------|
| `business_intel` | Company, audience, pricing, CTA |
| `design_audit` | Layout, colors, sections, quality |
| `competitor_analysis` | USPs, segment, strengths |
| `tech_stack` | Framework, CMS, analytics |
| `ux_patterns` | Navigation, hero, CTA patterns |
| `summary` | 3-5 sentence overview |
| `custom` | Use `custom_prompt` field |

### GET `/sitemap` — Discover Site Structure

```bash
curl "http://localhost:8100/sitemap?url=https://example.com&max_urls=100"
```

### GET `/vision/models` — List VLM Models

```bash
curl http://localhost:8100/vision/models
```

---

## Model Management Endpoints

### GET `/models` — List All Models

```bash
curl http://localhost:8100/models
```

### POST `/models/ollama/pull` — Pull Ollama Model (SSE)

```bash
curl -X POST http://localhost:8100/models/ollama/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "mistral"}' --no-buffer
```

### DELETE `/models/ollama/{name}` — Delete Ollama Model

```bash
curl -X DELETE http://localhost:8100/models/ollama/mistral
```

### POST `/models/openrouter` — Add Custom OR Model

```bash
curl -X POST http://localhost:8100/models/openrouter \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "qwen/qwen3-30b-a3b:free",
    "name": "Qwen3 30B",
    "free": true,
    "tier": "medium"
  }'
```

### GET `/models/openrouter/search` — Search OR Models

```bash
curl "http://localhost:8100/models/openrouter/search?q=claude&free_only=true"
```

### POST `/models/api` — Add Custom OpenAI-Compatible API

```bash
curl -X POST http://localhost:8100/models/api \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Groq",
    "base_url": "https://api.groq.com/openai/v1",
    "api_key": "gsk_...",
    "models": ["llama3-70b-8192"]
  }'
```

---

## History & Stats

### GET `/history` — Scrape History

```bash
curl "http://localhost:8100/history?limit=50&offset=0&url=example.com"
```

### GET `/stats` — Aggregate Statistics

```bash
curl http://localhost:8100/stats
```

**Response:**
```json
{
  "total_scrapes": 150,
  "total_cost_usd": 0.042,
  "avg_elapsed_ms": 1250.5,
  "top_providers": {"jina": 80, "scrapling": 50},
  "top_models": {"ollama/llama3.2": 100},
  "success_rate": 98.5
}
```

---

## Error Responses

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad Request — invalid parameters |
| `403` | Forbidden — invalid/missing API Key |
| `404` | Not Found — endpoint doesn't exist |
| `422` | Validation Error — Pydantic schema failed |
| `429` | Too Many Requests — rate limit exceeded |
| `500` | Internal Server Error |
