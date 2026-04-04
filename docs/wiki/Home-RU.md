# Домашняя страница

> **AI Scraping Stack** — 6-слойная платформа веб-разведки с ИИ. Скрейп, анализ, синтез, визуализация.

## Что такое AI Scraping Stack?

AI Scraping Stack превращает URL конкурентов в структурированную разведку и готовый код. Это полнофункциональная платформа, объединяющая **10+ провайдеров скрапинга**, **multi-agent синтез**, **VLM визуальный анализ** и **MCP интеграцию** в единую систему.

```
Вход: URL конкурентов
Выход: скриншоты + бизнес-анализ + дизайн-аудит + сгенерированный сайт
```

## Быстрые ссылки

| Страница | Описание |
|----------|----------|
| [Начало работы](Getting-Started-RU) | Установка, настройка, запуск за 5 минут |
| [Архитектура](Architecture-RU) | 6-слойная система и потоки данных |
| [API Справочник](API-Reference-RU) | Все эндпоинты, параметры, примеры |
| [Деплой](Deployment-RU) | Деплой на Render, Railway, Timeweb, Docker |
| [Участие](Contributing-RU) | Как внести вклад, стандарты кода, PR |

## Ключевые возможности

- **10+ провайдеров скрапинга** — Jina, Scrapling, Crawl4AI, ScraperAPI, Firecrawl, ZenRows, Scrapingdog, ScrapeGraphAI
- **Каскадный fallback** — если один провайдер упал, следующий подхватывает автоматически
- **Multi-Agent синтез** — Extractor → Ranker → Researcher → Architect → Coder
- **Визуальный интеллект** — Скриншоты анализируются VLM (business_intel, design_audit, competitor_analysis)
- **Бесплатный режим** — Всё работает без затрат: Jina + Ollama + OpenRouter free tier
- **MCP интеграция** — AI-агенты скрапят прямо из Claude/Cursor

## Архитектура в двух словах

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

## Быстрый старт

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
pip install -r requirements.txt
cp .env.example .env
uvicorn api:app --reload --port 8100
```

## Статус проекта

| Компонент | Статус |
|-----------|--------|
| Provider Router | ✅ Стабильно |
| LLM Router | ✅ Стабильно |
| Движок синтеза | ✅ Стабильно |
| Визуальный интеллект | ✅ Стабильно |
| MCP Server | ✅ Стабильно |
| Dashboard UI | ✅ Стабильно |
| Docker | ✅ Готово |
| CI/CD | ✅ Готово |

## Ссылки

- [GitHub репозиторий](https://github.com/homgorn/ai-scraping-stack)
- [Live демо](https://ai-scraping-stack.onrender.com)
- [Полная документация (README)](../README_RU.md)
- [Руководство (USAGE)](../USAGE_RU.md)
- [Дорожная карта](../ROADMAP_RU.md)
