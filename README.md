# AI Scraping Stack

> **6-layer intelligent web intelligence platform** — Scrape, Analyze, Synthesize, See.

[🇬🇧 English](#english) | [🇷🇺 Русский](#русский) | [🇨🇳 中文](#中文) | [🇪🇸 Español](#español) | [🇫🇷 Français](#français)

---

## English

### What is it?

AI Scraping Stack transforms competitor URLs into structured intelligence and ready-made code.

```
Input: competitor URLs
Output: screenshots + business analysis + design audit + generated website
```

### Architecture (6 Layers)

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

### Key Features

- **10+ Scraping Providers** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl, ZenRows, Scrapingdog, ScrapeGraphAI
- **Cascade Fallback** — if one provider fails, the next takes over automatically
- **Multi-Agent Synthesis** — Extractor → Ranker → Researcher → Architect → Coder
- **Visual Intelligence** — Screenshots analyzed by VLM (business_intel, design_audit, competitor_analysis)
- **Zero-Cost Mode** — Everything works free: Jina + Ollama + OpenRouter free tier
- **MCP Integration** — AI agents scrape directly from Claude/Cursor

### Quick Start

```bash
# 1. Install
pip install -r requirements.txt
scrapling install
ollama pull llama3.2

# 2. Configure
cp .env.example .env
# Edit .env with your keys

# 3. Run
uvicorn api:app --reload --port 8100
# Open http://localhost:8100
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scrape` | Single URL scrape + LLM analysis |
| POST | `/scrape/bulk` | N URLs parallel |
| POST | `/analyze` | Raw text → LLM analysis |
| POST | `/synthesize` | N URLs → website code |
| POST | `/screenshot` | Capture screenshot |
| POST | `/screenshot/audit` | Full visual audit |
| POST | `/vision/analyze` | VLM screenshot analysis |
| GET | `/sitemap` | Discover site structure |
| GET | `/history` | Scrape history |
| GET | `/stats` | Aggregate statistics |

### Provider Strategies

| Strategy | Providers | Cost |
|----------|-----------|------|
| `free` | Jina → Crawl4AI | $0 |
| `smart` | Jina → Scrapling → Crawl4AI → ScraperAPI | $0→paid |
| `stealth` | Scrapling Stealth → Scrapingdog → ScraperAPI | $0→paid |
| `premium` | Firecrawl → Crawl4AI | $0.002/page |

### Vision Tasks

| Task | Output | Use Case |
|------|--------|----------|
| `business_intel` | JSON: company, audience, pricing | Competitor research |
| `design_audit` | UX analysis: hierarchy, colors | Design inspiration |
| `competitor_analysis` | JSON: USPs, pricing tier | Market analysis |
| `tech_stack` | JSON: framework, UI library | Tech research |

### Docs

- [CONTEXT_MAP.md](CONTEXT_MAP.md) — Full system map
- [AGENT.md](AGENT.md) — AI agent context
- [ROADMAP.md](ROADMAP.md) — Development roadmap
- [USAGE.md](USAGE.md) — User guide
- [skills/](skills/) — Automation playbooks

### License

MIT

---

## Русский

### Что это?

AI Scraping Stack превращает URL конкурентов в структурированную разведку и готовый код.

```
Вход: URL конкурентов
Выход: скриншоты + бизнес-анализ + дизайн-аудит + сгенерированный сайт
```

### Быстрый старт

```bash
pip install -r requirements.txt
scrapling install && ollama pull llama3.2
cp .env.example .env
uvicorn api:app --reload --port 8100
```

### Ключевые возможности

- **10+ провайдеров** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl и другие
- **Каскадный fallback** — если один упал, следующий подхватывает
- **Multi-Agent синтез** — 5 AI-агентов создают сайт из URL конкурентов
- **Визуальный интеллект** — VLM анализирует скриншоты (бизнес, дизайн, конкуренты)
- **Бесплатный режим** — Всё работает без затрат: Jina + Ollama + OpenRouter free
- **MCP интеграция** — AI-агенты скрапят прямо из Claude/Cursor

### Стратегии провайдеров

| Стратегия | Провайдеры | Стоимость |
|-----------|-----------|-----------|
| `free` | Jina → Crawl4AI | $0 |
| `smart` | Jina → Scrapling → Crawl4AI → ScraperAPI | $0→платно |
| `stealth` | Scrapling Stealth → Scrapingdog → ScraperAPI | $0→платно |

### Задачи Vision

| Задача | Вывод | Применение |
|--------|-------|------------|
| `business_intel` | JSON: компания, аудитория, цены | Разведка конкурентов |
| `design_audit` | UX анализ: иерархия, цвета | Вдохновение для дизайна |
| `competitor_analysis` | JSON: УТП, ценовой сегмент | Анализ рынка |

---

## 中文

### 这是什么？

AI Scraping Stack 将竞争对手的 URL 转化为结构化情报和现成代码。

```
输入：竞争对手 URL
输出：截图 + 商业分析 + 设计审计 + 生成的网站
```

### 快速开始

```bash
pip install -r requirements.txt
scrapling install && ollama pull llama3.2
cp .env.example .env
uvicorn api:app --reload --port 8100
```

### 核心功能

- **10+ 抓取提供商** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl 等
- **级联回退** — 如果一个失败，下一个自动接管
- **多智能体合成** — 5 个 AI 代理从竞争对手 URL 生成网站
- **视觉智能** — VLM 分析截图（商业、设计、竞争对手）
- **零成本模式** — 全部免费运行：Jina + Ollama + OpenRouter 免费层
- **MCP 集成** — AI 代理直接从 Claude/Cursor 抓取

---

## Español

### ¿Qué es?

AI Scraping Stack transforma URLs de competidores en inteligencia estructurada y código listo.

```
Entrada: URLs de competidores
Salida: capturas + análisis de negocio + auditoría de diseño + sitio generado
```

### Inicio Rápido

```bash
pip install -r requirements.txt
scrapling install && ollama pull llama3.2
cp .env.example .env
uvicorn api:app --reload --port 8100
```

### Características Clave

- **10+ Proveedores** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl
- **Fallback en Cascada** — si uno falla, el siguiente toma el control
- **Síntesis Multi-Agente** — 5 agentes IA crean un sitio desde URLs
- **Inteligencia Visual** — VLM analiza capturas (negocio, diseño, competencia)
- **Modo Sin Costo** — Todo funciona gratis: Jina + Ollama + OpenRouter free
- **Integración MCP** — Agentes IA scrapean desde Claude/Cursor

---

## Français

### Qu'est-ce que c'est ?

AI Scraping Stack transforme les URLs des concurrents en intelligence structurée et code prêt.

```
Entrée: URLs des concurrents
Sortie: captures + analyse business + audit design + site généré
```

### Démarrage Rapide

```bash
pip install -r requirements.txt
scrapling install && ollama pull llama3.2
cp .env.example .env
uvicorn api:app --reload --port 8100
```

### Fonctionnalités Clés

- **10+ Fournisseurs** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl
- **Fallback en Cascade** — si l'un échoue, le suivant prend le relais
- **Synthèse Multi-Agent** — 5 agents IA créent un site depuis des URLs
- **Intelligence Visuelle** — VLM analyse les captures (business, design, concurrence)
- **Mode Zéro Coût** — Tout fonctionne gratuitement: Jina + Ollama + OpenRouter free
- **Intégration MCP** — Les agents IA scrapent depuis Claude/Cursor
