# AI Scraping Stack

> **6-слойная платформа веб-разведки с ИИ** — Скрейп, Анализ, Синтез, Визуализация.

[🇬🇧 English](README.md) | [🇷🇺 Русский](#русский)

---

## Русский

### Что это?

AI Scraping Stack превращает URL конкурентов в структурированную разведку и готовый код.

```
Вход: URL конкурентов
Выход: скриншоты + бизнес-анализ + дизайн-аудит + сгенерированный сайт
```

### Архитектура (6 слоёв)

```
┌─────────────────────────────────────────────────┐
│ L6: MCP Server     → AI-агенты вызывают как tool│
│ L5: Dashboard      → Человек управляет через UI │
│ L4: API Gateway    → FastAPI REST + SSE         │
│ L3: Intelligence   → LLM Router + Vision (VLM)  │
│ L2: Synthesis      → Multi-agent: N URL → сайт   │
│ L1: Provider Router→ 10+ провайдеров, каскад     │
└─────────────────────────────────────────────────┘
```

### Ключевые возможности

- **10+ провайдеров скрапинга** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl, ZenRows, Scrapingdog, ScrapeGraphAI
- **Каскадный fallback** — если один провайдер упал, следующий подхватывает автоматически
- **Multi-Agent синтез** — Extractor → Ranker → Researcher → Architect → Coder
- **Визуальный интеллект** — Скриншоты анализируются VLM (business_intel, design_audit, competitor_analysis)
- **Бесплатный режим** — Всё работает без затрат: Jina + Ollama + OpenRouter free tier
- **MCP интеграция** — AI-агенты скрапят прямо из Claude/Cursor

### Быстрый старт

```bash
# 1. Установка
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
pip install -r requirements.txt
scrapling install
ollama pull llama3.2

# 2. Настройка
cp .env.example .env
# Отредактируйте .env с вашными ключами

# 3. Запуск
uvicorn api:app --reload --port 8100
# Откройте landing.html в браузере
```

### API Эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/scrape` | Скрапинг одного URL + LLM анализ |
| POST | `/scrape/bulk` | N URL параллельно |
| POST | `/analyze` | Сырой текст → LLM анализ |
| POST | `/synthesize` | N URL → код сайта |
| POST | `/screenshot` | Сделать скриншот |
| POST | `/screenshot/audit` | Полный визуальный аудит |
| POST | `/vision/analyze` | VLM анализ скриншота |
| GET | `/sitemap` | Обнаружить структуру сайта |
| GET | `/history` | История скрапинга |
| GET | `/stats` | Агрегированная статистика |

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

### Документация

- [USAGE_RU.md](USAGE_RU.md) — Полное руководство (Русский)
- [USAGE.md](USAGE.md) — Complete user guide (English)
- [CONTEXT_MAP.md](CONTEXT_MAP.md) — Карта системы
- [AGENT.md](AGENT.md) — Контекст для AI-агентов
- [ROADMAP.md](ROADMAP.md) — Дорожная карта
- [skills/](skills/) — Автоматизация
- [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) — Деплой на Railway
- [DEPLOY_TIMEWEB.md](DEPLOY_TIMEWEB.md) — Деплой на Timeweb Cloud
- [DEPLOY_SHARED_HOSTING.md](DEPLOY_SHARED_HOSTING.md) — Деплой фронтенда на хостинг

### Лицензия

MIT
