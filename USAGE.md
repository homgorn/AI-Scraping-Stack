# USAGE.md — Полное руководство пользователя

## Быстрый старт

```bash
# 1. Клонируй репо
git clone <repo> && cd scrape-stack

# 2. Установка
pip install "scrapling[ai,fetchers]" fastapi "uvicorn[standard]" \
    httpx openai fastmcp python-dotenv pydantic pydantic-settings
scrapling install        # браузеры для StealthyFetcher

# 3. Конфиг
cp .env.example .env
# Открой .env, добавь ключи (минимум — всё работает и без них)

# 4. Ollama (локальная LLM — опционально, но рекомендуется)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2     # 2GB — базовая модель для анализа

# 5. Проверь систему
python -m src.debug --full

# 6. Запусти API
uvicorn api:app --reload --port 8100

# 7. Открой дашборд
open index.html          # или просто в браузере
```

---

## Навигация по документу

1. [Конфигурация](#конфигурация)
2. [Одиночный скрапинг](#одиночный-скрапинг)
3. [Массовый скрапинг](#массовый-скрапинг)
4. [Синтез сайта из URL](#синтез-сайта-из-url)
5. [Скриншоты и визуальный анализ](#скриншоты-и-визуальный-анализ)
6. [Управление моделями](#управление-моделями)
7. [MCP для AI-агентов](#mcp-для-ai-агентов)
8. [Python API](#python-api)
9. [Docker](#docker)
10. [Дебаггинг](#дебаггинг)
11. [FAQ](#faq)

---

## Конфигурация

### Минимальный `.env` (всё работает без ключей)

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Рекомендуемый `.env`

```env
# Локальная LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenRouter — 300+ моделей, бесплатный тир
# Получить: openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-...

# HuggingFace — бесплатные inference providers (~200 req/day)
# Получить: huggingface.co/settings/tokens
HF_TOKEN=hf_...

# Jina Reader — без ключа 20 RPM, с ключом — 10M токенов бесплатно
# Получить: jina.ai
JINA_API_KEY=jina_...
```

### Все настройки через API (без перезапуска)

```bash
curl -X PATCH http://localhost:8100/config \
  -H "Content-Type: application/json" \
  -d '{"openrouter_api_key": "sk-or-v1-..."}'
```

---

## Одиночный скрапинг

### Через дашборд (index.html)

1. Открой `index.html` в браузере
2. Введи URL в поле
3. Выбери режим, задачу, сложность
4. Нажми **Run Scrape**

### Через API

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

### Параметры scrape

| Параметр | Значения | По умолчанию | Описание |
|----------|----------|-------------|----------|
| `url` | URL | — | **Обязательный** |
| `mode` | fast / stealth / dynamic | fast | Тип fetcher |
| `strategy` | free / fast / smart / llm / ai / premium / stealth | smart | Провайдер |
| `task` | см. ниже | summarize | Что делать с контентом |
| `complexity` | low / medium / high | low | Выбор LLM |
| `css_selector` | CSS | "" | Извлечь конкретные элементы |
| `stream` | bool | false | SSE стриминг |

### Задачи (task)

| Task | Описание |
|------|----------|
| `summarize` | 3-5 предложений |
| `extract_entities` | JSON: люди, организации, цены |
| `classify` | news/product/blog/docs/ecommerce |
| `extract_prices` | JSON: продукты, цены, наличие |
| `sentiment` | JSON: тональность |
| `extract_links` | JSON: все ссылки |
| `translate_ru` | Перевод на русский |
| `qa:What is the price?` | Вопрос к тексту |
| `custom:List all emails` | Произвольная инструкция |

### Стратегии (strategy)

| Strategy | Провайдеры | Цена | Когда |
|----------|-----------|------|-------|
| `free` | Jina → Crawl4AI | $0 | Обычные сайты |
| `fast` | Scrapling | $0 | Быстро, bulk |
| `smart` | Jina→Scrapling→Crawl4AI→ScraperAPI | $0→$0.0005 | По умолчанию |
| `llm` | Crawl4AI | $0 | Нужен чистый markdown для RAG |
| `ai` | ScrapeGraphAI+Ollama | $0 | Prompt→JSON |
| `stealth` | Scrapling StealthyFetcher | $0 | Cloudflare |
| `premium` | Firecrawl | ~$0.002 | Лучшее качество |

### Сложность (complexity) → выбор LLM

```
low    → Ollama llama3.2 (локально, бесплатно, приватно)
medium → OpenRouter free (Qwen3 30B, Llama 3.3 70B)
high   → OpenRouter настроенная модель (Claude, GPT-4o)
```

---

## Массовый скрапинг

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

Возвращает: `{ results: [...], total: 3, success: 2, failed: 1 }`

---

## Синтез сайта из URL

Мощнейший режим: передаёшь 1–50 URL конкурентов → получаешь полный сайт.

### Пайплайн

```
Scrape N URLs → Extract patterns → Jina Search trends → Rank insights → Architect → Code
```

### Через API

```bash
# Один формат
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

### Форматы вывода

| `output_format` | Что получишь |
|----------------|-------------|
| `html` | Готовый `<!DOCTYPE html>` файл, открываешь в браузере |
| `react` | React компонент, вставляешь в Vite/CRA |
| `fullstack_spec` | Markdown спек: BD schema, API, docker compose |

### Несколько вариантов

```bash
curl -X POST http://localhost:8100/synthesize/multi \
  -d '{"urls": [...], "prompt": "...", "num_variants": 2}'
# Возвращает html + react версии
```

### Примеры хороших промптов

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

## Скриншоты и визуальный анализ

### Скриншот одного URL

```bash
curl -X POST http://localhost:8100/screenshot \
  -d '{"url": "https://example.com", "full_page": true, "save": true}'
# Возвращает: screenshot_b64 (PNG), provider, elapsed_ms
```

### Полный аудит сайта (рекомендуется)

```bash
curl -X POST http://localhost:8100/screenshot/audit \
  -d '{
    "url": "https://competitor.com",
    "max_pages": 10,
    "tasks": ["business_intel", "design_audit", "competitor_analysis"],
    "save_screenshots": true
  }'
```

**Что происходит:**
1. Парсится `robots.txt` + `sitemap.xml`
2. Находятся ключевые страницы (`/about`, `/pricing`, `/features`, ...)
3. Делаются скриншоты всех страниц параллельно (Crawl4AI)
4. VLM анализирует каждый скриншот

**Возвращает:**
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

### Bulk скриншоты + VLM

```bash
curl -X POST http://localhost:8100/screenshot/bulk \
  -d '{
    "urls": ["https://a.com", "https://b.com", "https://c.com"],
    "tasks": ["business_intel", "tech_stack"],
    "max_concurrent": 3,
    "save": true
  }'
```

### VLM задачи для анализа скриншотов

| Task | Возвращает | Для чего |
|------|-----------|---------|
| `business_intel` | JSON: company, audience, pricing | Исследование рынка |
| `design_audit` | JSON: layout, colors, quality score | Дизайн-анализ |
| `competitor_analysis` | JSON: USPs, segment, strengths | Конкурентный анализ |
| `tech_stack` | JSON: framework, CMS, analytics | Технологии конкурента |
| `ux_patterns` | JSON: nav, hero, CTA, social proof | Сбор паттернов |
| `ocr_extract` | Весь текст с разметкой секций | Извлечение текста |
| `summary` | 3-5 предложений | Быстрый обзор |

### Ручной анализ скриншота

```bash
# Сначала скришот
RESULT=$(curl -s -X POST http://localhost:8100/screenshot -d '{"url":"..."}')
B64=$(echo $RESULT | python3 -c "import json,sys; print(json.load(sys.stdin)['screenshot_b64'])")

# Потом VLM анализ
curl -X POST http://localhost:8100/vision/analyze \
  -d "{\"screenshot_b64\": \"$B64\", \"task\": \"competitor_analysis\"}"
```

### Узнать структуру сайта (robots.txt + sitemap)

```bash
curl "http://localhost:8100/sitemap?url=https://example.com&max_urls=100"
# Возвращает: sitemap_urls (все страницы), key_pages, disallowed
```

---

## Управление моделями

### Ollama — локальные LLM

```bash
# Список установленных
curl http://localhost:8100/models | python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin)['ollama']]"

# Установить новую модель (SSE stream)
curl -X POST http://localhost:8100/models/ollama/pull \
  -d '{"model_name": "mistral"}' \
  --no-buffer

# Удалить
curl -X DELETE http://localhost:8100/models/ollama/mistral
```

### Ollama — LLM модели (текст)
```bash
ollama pull llama3.2      # 2GB, быстрый, базовый
ollama pull mistral       # 4.1GB, хороший для извлечения
ollama pull qwen2.5       # 4.4GB, мультиязычный
ollama pull deepseek-r1   # рассуждение, задачи
```

### Ollama — Vision модели (для скриншотов)
```bash
ollama pull qwen2.5vl:7b  # 4.7GB, лучший/компактный
ollama pull llava:7b      # 4.7GB, надёжный классик
ollama pull moondream     # 0.8GB, быстрый, CPU
```

### Установить VLM из HuggingFace GGUF

```bash
# Через API (SSE stream прогресса, авто-регистрация)
curl -X POST http://localhost:8100/models/ollama/install-hf \
  -d '{
    "hf_repo": "Qwen/Qwen3-VL-30B-A3B-Instruct-GGUF",
    "gguf_file": "qwen3vl-30b-a3b-instruct-q4_k_m.gguf",
    "model_name": "qwen3-vl-30b"
  }' --no-buffer

# Или напрямую через ollama
ollama pull hf.co/Qwen/Qwen3-VL-30B-A3B-Instruct-GGUF:qwen3vl-30b-a3b-instruct-q4_k_m.gguf
```

### OpenRouter — список и добавление

```bash
# Список всех бесплатных vision
curl http://localhost:8100/models/vision

# Добавить кастомную OR модель
curl -X POST http://localhost:8100/models/vision/add \
  -d '{
    "id": "mistralai/pixtral-large-2411",
    "name": "Pixtral Large",
    "provider": "openrouter",
    "free": false
  }'

# Обновить список бесплатных OR моделей (запроси live из API)
curl -X POST http://localhost:8100/models/vision/refresh
```

### HuggingFace — поиск моделей

```bash
# Поиск VLM моделей на HuggingFace Hub
curl "http://localhost:8100/models/hf/search?q=vision+language&limit=10"

# Добавить HF модель в реестр
curl -X POST http://localhost:8100/models/vision/add \
  -d '{
    "id": "Qwen/Qwen2.5-VL-7B-Instruct",
    "hf_id": "Qwen/Qwen2.5-VL-7B-Instruct",
    "name": "Qwen2.5-VL 7B HF",
    "provider": "huggingface"
  }'
```

### Добавить свой OpenAI-совместимый эндпоинт

```bash
# vLLM, llama.cpp server, LM Studio, Groq, Together, Perplexity...
curl -X POST http://localhost:8100/models/api \
  -d '{
    "name": "Groq",
    "base_url": "https://api.groq.com/openai/v1",
    "api_key": "gsk_...",
    "models": ["llama3-70b-8192", "mixtral-8x7b-32768"],
    "description": "Ultra-fast inference"
  }'
```

---

## MCP для AI-агентов

Подключи скрапер как инструмент к Claude Desktop, Cursor, Windsurf.

### Claude Desktop

Добавь в `~/.claude/mcp_config.json`:

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

Перезапусти Claude Desktop. Появятся 6 инструментов:
- `get` / `bulk_get` — быстрый fetch
- `fetch` / `bulk_fetch` — с рендерингом JS
- `stealthy_fetch` / `bulk_stealthy_fetch` — обход Cloudflare

### Расширенный MCP (с Ollama + OpenRouter)

```bash
python stack.py serve
```

---

## Python API

### Простой скрапинг

```python
import asyncio
from providers import ProviderRouter

async def main():
    router = ProviderRouter({
        "jina_api_key": "jina_...",    # опционально
    })
    
    # Одна страница
    result = await router.scrape("https://example.com", strategy="smart")
    print(result.markdown)   # LLM-ready текст
    print(result.provider)   # кто обработал
    print(result.cost_usd)   # стоимость

asyncio.run(main())
```

### Анализ с LLM

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
print(result.analysis)       # JSON строка
print(result.model_used)     # "ollama/llama3.2"
print(result.elapsed_ms)     # время в мс
```

### Скриншоты

```python
from src.screenshot import ScreenshotService, SiteMapService
from src.vision import VisionService, ModelRegistry
from src.config import get_settings

cfg = get_settings()
screenshots = ScreenshotService(cfg)
sitemap = SiteMapService(cfg)
registry = ModelRegistry()
vision = VisionService(cfg, registry)

# Обновить список бесплатных OR моделей
await registry.fetch_live_or_vision_models(cfg.openrouter_api_key)

# Узнать структуру сайта
site = await sitemap.discover("https://competitor.com")
print(site.key_pages)    # ["/about", "/pricing", ...]
print(len(site.sitemap_urls))  # сколько всего страниц

# Скриншот главной + ключевых страниц
shots = await screenshots.capture_many(
    [site.url] + site.key_pages[:9],
    max_concurrent=3,
    output_dir="data/screenshots",
)

# VLM анализ каждого
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

### Синтез сайта

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
    research_trends=True,         # Jina Search для трендов
    complexity="high",            # использовать лучшую LLM
)

# Сохрани готовый сайт
with open("output_site.html", "w") as f:
    f.write(result.code)

print("Insights:", result.insights[:3])
print("Trends:", result.trends[:3])
print("Elapsed:", result.elapsed_ms, "ms")
```

### История и статистика

```python
from src.storage import Storage

storage = Storage(cfg)
await storage.init()

# Последние 50 scrapes
history = await storage.get_history(limit=50)

# Фильтр по URL
github = await storage.get_history(url_filter="github.com")

# Статистика сессии
stats = await storage.get_stats()
print(f"Total: {stats['total']}, Cost: ${stats['total_cost_usd']:.4f}")
```

---

## Docker

### Запуск всего стека

```bash
# API + Ollama
docker compose up -d

# Посмотреть логи
docker compose logs -f api

# Проверить статус
curl http://localhost:8100/status
```

### Загрузить модели в Docker Ollama

```bash
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull qwen2.5vl:7b
```

### Остановить

```bash
docker compose down
```

Данные (SQLite, модели Ollama) персистентны через volumes.

---

## Дебаггинг

### Health check

```bash
# Быстрая проверка всех компонентов
python -m src.debug

# С live тестом скрапинга
python -m src.debug --full

# Показать что не работает и как починить
python -m src.debug --fix
```

Пример вывода:
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

### Тесты

```bash
# Все тесты
python -m pytest tests/ -v

# Конкретный модуль
python -m pytest tests/test_vision.py -v
python -m pytest tests/test_storage.py -v

# С покрытием
python -m pytest tests/ --cov=src --cov=providers --cov-report=term-missing

# Только быстрые (без async)
python -m pytest tests/ -v -k "not asyncio"
```

### Частые проблемы

**Ollama не отвечает**
```bash
ollama serve                    # запустить вручную
curl http://localhost:11434/api/tags   # проверить
```

**`ModuleNotFoundError: scrapling`**
```bash
pip install "scrapling[ai,fetchers]"
scrapling install               # браузеры
```

**Crawl4AI браузер не найден**
```bash
pip install crawl4ai
crawl4ai-setup                  # загрузить Playwright браузеры
```

**OpenRouter 401**
```bash
# Проверь ключ
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-..."
```

**Скриншот не делается**
```bash
# Проверь Playwright
playwright install chromium
# или Crawl4AI
crawl4ai-setup
```

**`data/` директория не создаётся**
```bash
mkdir -p data
```

---

## FAQ

**Q: Можно ли скрапить без Ollama и OpenRouter?**
A: Да. Jina Reader работает вообще без ключей. Скрапинг работает, анализ — нет.

**Q: Сколько стоит 1000 страниц?**
A: При стратегии `smart` — $0 (Jina + Scrapling). С ScraperAPI fallback — до $0.49.

**Q: Cloudflare блокирует?**
A: Используй `mode=stealth` или `strategy=stealth`. Scrapling StealthyFetcher обходит CF Turnstile.

**Q: Как получить LLM-ready markdown (для RAG)?**
A: `strategy=llm` (Crawl4AI) или `strategy=free` (Jina Reader). Оба возвращают чистый markdown.

**Q: Синтез занимает долго — как ускорить?**
A: Уменьши `complexity=medium` (OR free вместо Claude). Меньше URL. Отключи `research_trends=false`.

**Q: Как добавить новую vision модель вышедшую сегодня?**
A: `POST /models/vision/refresh` — автообновление с OR API. Или `POST /models/vision/add` вручную.

**Q: Как использовать как библиотеку (без FastAPI)?**
A: Импортируй напрямую: `from providers import ProviderRouter`, `from src.vision import VisionService` и т.д.

**Q: Где хранится история скрапинга?**
A: `data/history.db` (SQLite). `GET /history` через API. `GET /stats` для статистики.

**Q: Как подключить Groq / Together / Perplexity?**
A: `POST /models/api` с `base_url`, `api_key`, `models`. Все OpenAI-совместимые API работают.
