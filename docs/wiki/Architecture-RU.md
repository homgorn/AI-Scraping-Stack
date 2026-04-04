# Архитектура

> Понимание 6-слойной системы, потоков данных и ответственности модулей.

## Обзор системы

AI Scraping Stack построен на **6-слойной архитектуре**, где каждый слой имеет единую ответственность и взаимодействует через чёткие интерфейсы.

```
┌─────────────────────────────────────────────────────────┐
│  СЛОЙ 6: MCP Server                                    │
│  "scrapling mcp" — 6 инструментов для Claude / Cursor   │
├─────────────────────────────────────────────────────────┤
│  СЛОЙ 5: Dashboard UI                                  │
│  landing.html — SEO-оптимизированный, двуязычный        │
├─────────────────────────────────────────────────────────┤
│  СЛОЙ 4: API Gateway (FastAPI)                         │
│  api.py — ВСЕ маршруты, middleware, безопасность        │
├─────────────────────────────────────────────────────────┤
│  СЛОЙ 3: Intelligence Engine                           │
│  src/llm.py   → LLM Router (Ollama + OpenRouter)       │
│  src/vision.py → VisionService + VLM анализ             │
├─────────────────────────────────────────────────────────┤
│  СЛОЙ 2: Synthesis Engine                              │
│  src/synthesizer.py — Multi-agent: N URL → сайт         │
├─────────────────────────────────────────────────────────┤
│  СЛОЙ 1: Provider Router                               │
│  providers.py — 10+ адаптеров, каскадный fallback       │
└─────────────────────────────────────────────────────────┘
```

## Карта модулей

```
scrapling/
├── src/                          # Модули бизнес-логики
│   ├── config.py                 # Pydantic Settings (все env vars)
│   ├── models.py                 # Все Pydantic схемы
│   ├── llm.py                    # LLMRouter: Ollama + OpenRouter
│   ├── scraper.py                # ScraperService: оркестрация
│   ├── storage.py                # SQLite история + JSON реестр
│   ├── screenshot.py             # ScreenshotService + SiteMapService
│   ├── vision.py                 # VisionService + VisualAuditPipeline
│   ├── synthesizer.py            # WebSynthesizer: multi-agent pipeline
│   └── sitemap.py                # Re-export SiteMapService
├── api.py                        # FastAPI движок (все маршруты)
├── providers.py                  # ProviderRouter + 8 адаптеров
├── stack.py                      # MCP Server + автономное демо
├── landing.html                  # SEO фронтенд (EN)
├── landing_ru.html               # SEO фронтенд (RU)
├── render.yaml                   # Render.com Blueprint
├── requirements.txt              # Зависимости
└── .github/workflows/            # CI/CD + Keep-Alive
```

## Потоки данных

### Поток 1: Скрапинг одного URL + Анализ

```
POST /scrape → api.py
  → ScraperService.scrape(req)
    → ProviderRouter.scrape(url, strategy)
      → JinaAdapter → ScraplingFast → Crawl4AI → ScraperAPI (каскад)
    → возвращает ScrapeResult
  → LLMRouter.analyze(text, task, complexity)
    → _call_ollama() [low] или _call_openrouter() [medium/high]
  → Storage.save_result()
  → возвращает ScrapeResponse (JSON)
```

### Поток 2: Синтез (N URL → Сайт)

```
POST /synthesize → api.py
  → WebSynthesizer.run(urls, prompt, format)
    → _scrape_all(urls) [параллельно, ≤5 одновременно]
    → _extract_all(contents) [Extractor агент x N]
    → _research_trends(topic) [Jina Search x 2]
    → _rank_insights(extractions) [Ranker агент]
    → _architect(prompt, insights, trends) [Architect агент]
    → _generate_code(spec, format) [Coder агент]
    → возвращает { code, insights, trends, spec, stack }
```

### Поток 3: Скриншоты + Визуальный аудит

```
POST /screenshot/audit → api.py
  → VisualAuditPipeline.run(url, max_pages, tasks)
    → SiteMapService.discover(url) → ключевые страницы
    → ScreenshotService.capture_many(pages) → base64 PNGs
    → VisionService.analyze_many(screenshots, task) → VLM инсайты
    → возвращает { key_pages, pages_analyzed, key_insights }
```

## Порядок зависимостей (без циклических импортов)

```
config → models → llm → scraper → synthesizer → api
                   → storage → api
                   → screenshot → vision → api
providers ← автономный (без импортов из src/)
stack.py  ← автономный (без импортов FastAPI)
```

## Middleware безопасности

Все POST/PUT/DELETE запросы проходят через `security_middleware` в `api.py`:

1. **Rate Limiting** — Макс. 10 запросов/мин с одного IP
2. **API Key** — Если задан `API_KEY`, требуется заголовок `X-API-Key`
3. **CORS** — Настраиваемые origins (по умолчанию: `*` для dev)

## Каскад провайдеров

| Стратегия | Провайдеры | Стоимость | Применение |
|-----------|-----------|-----------|------------|
| `free` | Jina → Crawl4AI | $0 | Обычные сайты |
| `fast` | Scrapling | $0 | Быстрый, массовый скрапинг |
| `smart` | Jina → Scrapling → Crawl4AI → ScraperAPI | $0 → $0.0005 | По умолчанию |
| `llm` | Crawl4AI | $0 | Чистый markdown для RAG |
| `ai` | ScrapeGraphAI + Ollama | $0 | Prompt → JSON |
| `stealth` | Scrapling StealthyFetcher | $0 | Сайты с Cloudflare |
| `premium` | Firecrawl | ~$0.002 | Лучшее качество |

## Маршрутизация LLM

| Сложность | Модель | Стоимость | Скорость |
|-----------|--------|-----------|----------|
| `low` | Ollama (llama3.2) | Бесплатно | Быстро (локально) |
| `medium` | OpenRouter free (Qwen3 30B) | Бесплатно | Средняя |
| `high` | OpenRouter (Claude, GPT-4o) | Платно | Средняя |

## Хранилище

| Компонент | Тип | Назначение |
|-----------|-----|------------|
| `data/scrapling.db` | SQLite | История скрейпов, статистика |
| `data/models.json` | JSON | Реестр кастомных моделей |
| `data/screenshots/` | Файлы | Скриншоты |

## Апгрейды для высокой нагрузки

| Компонент | Стандарт | High-Load |
|-----------|----------|-----------|
| БД | SQLite | PostgreSQL + PgBouncer |
| Кэш | In-memory | Redis |
| Сервер | Uvicorn | Gunicorn + Uvicorn workers |
| Очередь | asyncio.Semaphore | Celery + RabbitMQ |
| Мониторинг | Логи | Prometheus + Grafana |
| Трейсинг | Нет | OpenTelemetry |
