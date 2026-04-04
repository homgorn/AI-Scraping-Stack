# Home

> **AI Scraping Stack** — 6-layer intelligent web intelligence platform. Scrape, analyze, synthesize, and see the web through AI.

## What is AI Scraping Stack?

AI Scraping Stack transforms competitor URLs into structured intelligence and ready-made code. It's a full-stack platform that combines **10+ scraping providers**, **multi-agent synthesis**, **VLM visual analysis**, and **MCP integration** into one unified system.

```
Input: competitor URLs
Output: screenshots + business analysis + design audit + generated website
```

## Quick Links

| Page | Description |
|------|-------------|
| [Getting Started](Getting-Started) | Install, configure, and run in 5 minutes |
| [Architecture](Architecture) | 6-layer system design and data flows |
| [API Reference](API-Reference) | All endpoints, parameters, and examples |
| [Deployment](Deployment) | Deploy to Render, Railway, Timeweb, Docker |
| [Contributing](Contributing) | How to contribute, code standards, PR guide |

## Key Features

- **10+ Scraping Providers** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl, ZenRows, Scrapingdog, ScrapeGraphAI
- **Cascade Fallback** — if one provider fails, the next takes over automatically
- **Multi-Agent Synthesis** — Extractor → Ranker → Researcher → Architect → Coder
- **Visual Intelligence** — Screenshots analyzed by VLM (business_intel, design_audit, competitor_analysis)
- **Zero-Cost Mode** — Everything works free: Jina + Ollama + OpenRouter free tier
- **MCP Integration** — AI agents scrape directly from Claude/Cursor

## Architecture at a Glance

```
┌─────────────────────────────────────────────────┐
│ L6: MCP Server     → AI agents call as tools    │
│ L5: Dashboard      → Human controls via UI      │
│ L4: API Gateway    → FastAPI REST + SSE         │
│ L3: Intelligence   → LLM Router + Vision (VLM)  │
│ L2: Synthesis      → Multi-agent: N URLs → site  │
│ L1: Provider Router→ 10+ providers, cascade      │
└─────────────────────────────────────────────────┘
```

## Quick Start

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
pip install -r requirements.txt
cp .env.example .env
uvicorn api:app --reload --port 8100
```

## Project Status

| Component | Status |
|-----------|--------|
| Provider Router | ✅ Stable |
| LLM Router | ✅ Stable |
| Synthesis Engine | ✅ Stable |
| Visual Intelligence | ✅ Stable |
| MCP Server | ✅ Stable |
| Dashboard UI | ✅ Stable |
| Docker | ✅ Ready |
| CI/CD | ✅ Ready |

## Links

- [GitHub Repository](https://github.com/homgorn/ai-scraping-stack)
- [Live Demo](https://ai-scraping-stack.onrender.com)
- [Full Documentation (README)](../README.md)
- [Usage Guide](../USAGE.md)
- [Roadmap](../ROADMAP.md)
