# API Справочник

> Полный справочник всех REST эндпоинтов, параметров и форматов ответов.

**Базовый URL:** `http://localhost:8100` (локально) или ваш URL деплоя.

## Аутентификация

Если `API_KEY` задан в переменных окружения, все POST/PUT/DELETE запросы требуют:
```
X-API-Key: ваш-секретный-ключ
```

GET эндпоинты (health, status, models) всегда открыты.

---

## Основные эндпоинты

### GET `/` — Проверка здоровья

Возвращает статус сервиса и версию.

```bash
curl http://localhost:8100/
```

**Ответ:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### GET `/status` — Статус сервиса

Возвращает детальный статус всех компонентов.

```bash
curl http://localhost:8100/status
```

### GET `/config` — Текущая конфигурация

Возвращает текущую конфигурацию (ключи замаскированы).

### PATCH `/config` — Обновить конфигурацию

Обновление конфигурации в реальном времени (сохраняется в JSON).

```bash
curl -X PATCH http://localhost:8100/config \
  -H "Content-Type: application/json" \
  -d '{"max_concurrent": 10}'
```

---

## Эндпоинты скрапинга

### POST `/scrape` — Один URL

Скрапинг одного URL с опциональным LLM анализом.

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

**Параметры:**

| Параметр | Тип | Значения | По умолч. | Обяз. |
|----------|-----|----------|-----------|-------|
| `url` | string | URL | — | ✅ |
| `strategy` | string | free/fast/smart/llm/ai/premium/stealth | smart | ❌ |
| `task` | string | summarize/extract_entities/classify/extract_prices/sentiment | summarize | ❌ |
| `complexity` | string | low/medium/high | low | ❌ |

### POST `/scrape/bulk` — Несколько URL

Скрапинг до 50 URL параллельно.

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

### POST `/analyze` — Анализ сырого текста

Анализ текста через LLM (без скрапинга).

```bash
curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Длинный текст для анализа...",
    "task": "extract_entities",
    "complexity": "medium"
  }'
```

---

## Эндпоинты синтеза

### POST `/synthesize` — Генерация сайта

Генерация сайта из URL конкурентов.

```bash
curl -X POST http://localhost:8100/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://competitor1.com", "https://competitor2.com"],
    "prompt": "Создай лендинг SaaS. Тёмная тема.",
    "output_format": "html",
    "research_trends": true,
    "complexity": "high"
  }'
```

### POST `/synthesize/multi` — Несколько вариантов

Генерация нескольких вариантов сайта.

```bash
curl -X POST http://localhost:8100/synthesize/multi \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://competitor1.com"],
    "prompt": "Создай лендинг",
    "num_variants": 2
  }'
```

---

## Эндпоинты скриншотов и Vision

### POST `/screenshot` — Скриншот

```bash
curl -X POST http://localhost:8100/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "width": 1440,
    "full_page": true,
    "save": false
  }'
```

### POST `/screenshot/bulk` — Массовые скриншоты

```bash
curl -X POST http://localhost:8100/screenshot/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://a.com", "https://b.com"],
    "tasks": ["business_intel", "design_audit"],
    "max_concurrent": 3
  }'
```

### POST `/screenshot/audit` — Полный визуальный аудит

Обнаружение sitemap → скриншоты всех страниц → VLM анализ.

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

### POST `/vision/analyze` — Анализ скриншота

Анализ скриншота через VLM.

```bash
curl -X POST http://localhost:8100/vision/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "screenshot_b64": "iVBORw0KGgo...",
    "task": "business_intel",
    "url": "https://example.com"
  }'
```

**Задачи Vision:**

| Задача | Описание |
|--------|----------|
| `business_intel` | Компания, аудитория, цены, CTA |
| `design_audit` | Макет, цвета, секции, качество |
| `competitor_analysis` | УТП, сегмент, сильные стороны |
| `tech_stack` | Фреймворк, CMS, аналитика |
| `ux_patterns` | Навигация, hero, CTA паттерны |
| `summary` | Обзор в 3-5 предложениях |
| `custom` | Используйте поле `custom_prompt` |

### GET `/sitemap` — Обнаружение структуры сайта

```bash
curl "http://localhost:8100/sitemap?url=https://example.com&max_urls=100"
```

### GET `/vision/models` — Список VLM моделей

```bash
curl http://localhost:8100/vision/models
```

---

## Управление моделями

### GET `/models` — Список всех моделей

```bash
curl http://localhost:8100/models
```

### POST `/models/ollama/pull` — Загрузка модели Ollama (SSE)

```bash
curl -X POST http://localhost:8100/models/ollama/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "mistral"}' --no-buffer
```

### DELETE `/models/ollama/{name}` — Удаление модели Ollama

```bash
curl -X DELETE http://localhost:8100/models/ollama/mistral
```

### POST `/models/openrouter` — Добавить кастомную OR модель

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

### GET `/models/openrouter/search` — Поиск моделей OR

```bash
curl "http://localhost:8100/models/openrouter/search?q=claude&free_only=true"
```

### POST `/models/api` — Добавить совместимый OpenAI API

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

## История и статистика

### GET `/history` — История скрейпов

```bash
curl "http://localhost:8100/history?limit=50&offset=0&url=example.com"
```

### GET `/stats` — Агрегированная статистика

```bash
curl http://localhost:8100/stats
```

**Ответ:**
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

## Коды ошибок

| Код | Значение |
|-----|----------|
| `400` | Неверный запрос — невалидные параметры |
| `403` | Запрещено — неверный/отсутствующий API Key |
| `404` | Не найдено — эндпоинт не существует |
| `422` | Ошибка валидации — Pydantic схема не прошла |
| `429` | Слишком много запросов — превышен лимит |
| `500` | Внутренняя ошибка сервера |
