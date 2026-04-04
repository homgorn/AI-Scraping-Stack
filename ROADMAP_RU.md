# ROADMAP.md — Дорожная карта

> AI Scraping Stack — Дорожная карта разработки

---

## Обозначения
- ✅ Готово
- 🔄 В процессе / частично
- 📋 Запланировано
- 💡 Идеи / будущее

---

## v0.1 — Фундамент ✅

- ✅ 4-слойная архитектура: Scrapling → Ollama → MCP → OpenRouter
- ✅ FastAPI REST бэкенд (`api.py`)
- ✅ Dashboard UI (`index.html`) — тёмная терминальная эстетика
- ✅ Интеграция Scrapling v0.4 (fast/stealth/dynamic режимы)
- ✅ Ollama локальная LLM (llama3.2/mistral/qwen)
- ✅ OpenRouter SDK (300+ моделей, маршрутизация free tier)
- ✅ MCP сервер (scrapling mcp — 6 инструментов для Claude Desktop/Cursor)
- ✅ Массовый скрапинг с управлением конкурентностью

---

## v0.2 — Очистка архитектуры ✅

- ✅ `src/config.py` — Pydantic Settings (замена глобального dict)
- ✅ `src/models.py` — централизованные Pydantic схемы
- ✅ `src/llm.py` — сервис маршрутизации LLM (SRP)
- ✅ `src/scraper.py` — сервис скрапинга (SRP)
- ✅ `src/storage.py` — SQLite история + JSON реестр моделей
- ✅ `providers.py` — унифицированный адаптер: 8 провайдеров, ProviderRouter
- ✅ `requirements.txt` — Python зависимости
- ✅ `.env.example` — все env vars с комментариями
- ✅ `stack.py` — автономное демо + MCP сервер
- ✅ Тесты: `test_llm.py`, `test_providers.py`
- ✅ Все маршруты объединены в `api.py`
- ✅ `/history` и `/stats` подключены к Storage
- ✅ `/analyze` эндпоинт для анализа текста

---

## v0.3 — Движок синтеза ✅

- ✅ `src/synthesizer.py` — multi-agent pipeline
- ✅ `POST /synthesize` — N URL + промпт → код сайта
- ✅ `POST /synthesize/multi` — возвращает несколько вариантов
- ✅ Pipeline агентов: Extractor → Ranker → Researcher → Architect → Coder
- ✅ Интеграция Jina Search для исследования трендов
- ✅ Форматы вывода: HTML / React / Full-stack spec
- ✅ Документация навыков: `skills/skill_synthesize.md`

---

## v0.3.1 — Слой визуального интеллекта ✅

- ✅ `src/screenshot.py` — ScreenshotService (Crawl4AI→Playwright→Scrapling каскад)
- ✅ `src/vision.py` — VisionService + VisualAuditPipeline + ModelRegistry
- ✅ `src/sitemap.py` — обнаружение robots.txt + sitemap.xml
- ✅ `POST /screenshot` — скриншот одного URL
- ✅ `POST /screenshot/bulk` — N скриншотов + VLM анализ
- ✅ `POST /screenshot/audit` — полный визуальный аудит
- ✅ `POST /vision/analyze` — анализ скриншота через VLM
- ✅ `GET /sitemap` — обнаружение структуры сайта
- ✅ `GET /vision/models` — список доступных VLM
- ✅ `skills/skill_screenshot.md` — полное руководство

### Бесплатные VLM модели
- **Локальные**: qwen2.5vl:7b, llava:7b, moondream (Ollama)
- **Облачные**: gemma-3n-e4b-it:free, llama-3.2-11b-vision:free (OpenRouter)

### Задачи Vision
- business_intel, design_audit, competitor_analysis
- tech_stack, ux_patterns, content_extract, summary, custom

---

## v0.4 — SEO Лендинг + Деплой ✅

- ✅ `landing.html` — SEO-оптимизированный фронтенд (Schema.org, FAQ, Open Graph)
- ✅ 5 вкладок: Scrape, Synthesize, Screenshot, Audit, Vision
- ✅ Статический HTML — размещается на любом shared hosting
- ✅ Связь с бэкендом через `API_URL` (fetch)
- ✅ `DEPLOY_RAILWAY.md` — инструкция деплоя бэкенда на Railway
- ✅ `DEPLOY_TIMEWEB.md` — инструкция деплоя на Timeweb Cloud (с GPU/Ollama)
- ✅ `DEPLOY_SHARED_HOSTING.md` — инструкция деплоя фронтенда на виртуальный хостинг
- ✅ Nginx конфиг для проксирования `/api/` → бэкенд
- ✅ systemd сервис для автозапуска API
- ✅ Dockerfile + docker-compose.yml
- ✅ .gitignore
- ✅ Makefile
- ✅ pyproject.toml

---

## v0.5 — Полноценный Dashboard 📋

- 📋 Вкладка Synthesis: ввод URL, промпт, выбор формата, прогресс в реальном времени
- 📋 Вкладка Visual Audit: навигатор sitemap, галерея скриншотов, VLM инсайты
- 📋 Вкладка History: прошлые скрейпы + синтезы, перезапуск, экспорт
- 📋 Предпросмотр кода с подсветкой синтаксиса (Prism.js CDN)
- 📋 Кнопка скачивания → сохраняет .html / .jsx / .md файл

---

## v0.5 — Хранилище и История 🔄

- ✅ Подключение `Storage` к маршрутам скрапинга
- ✅ `GET /history` с фильтрацией
- ✅ `GET /stats` — агрегированная статистика
- 📋 Панель истории в дашборде
- 📋 Экспорт истории: CSV / JSON
- 📋 Дедупликация: пропуск повторного скрейпа того же URL если кеш < N часов
- 📋 Сохранение результатов синтеза в SQLite

---

## v0.6 — Планировщик 📋

- 📋 `POST /schedule` — cron задачи скрапинга
- 📋 Интеграция APScheduler
- 📋 Webhook уведомления
- 📋 Управление расписанием в дашборде

---

## v0.7 — RAG Pipeline 📋

- 📋 `POST /rag/index` — scrape → chunk → embed → store
- 📋 `POST /rag/query` — семантический поиск
- 📋 `POST /rag/chat` — чат с индексированными сайтами
- 📋 Дашборд: вкладка "База знаний"

---

## v0.8 — Улучшения агентов 📋

- 📋 Итеративный синтез: агент ревьюит код, улучшает за 3 раунда
- 📋 Агент анализа конкурентов
- 📋 Агент SEO анализа
- 📋 Агент мониторинга цен
- 📋 Анализ пробелов в контенте

---

## v0.9 — Продакшен 📋

- 📋 Rate limiting (slowapi)
- 📋 API ключ аутентификация
- 📋 CORS: ограничение с `*`
- 📋 Структурированное логирование
- 📋 Prometheus метрики
- 📋 Пул соединений httpx
- 📋 Корректное завершение работы

---

## v1.0 — Публичный релиз 💡

- 💡 OpenAPI документация
- 💡 CLI: `scrapling scrape <url>` / `scrapling synthesize <urls> "<prompt>"`
- 💡 PyPI пакет
- 💡 Docker Hub образ
- 💡 Кнопка деплоя в один клик
- 💡 GitHub Actions CI/CD

---

## Трекер технического долга

| Проблема | Файл | Приоритет |
|----------|------|-----------|
| Closure bug в `_build_chain` lambda | providers.py | Высокий |
| httpx клиент на запрос (без пула) | providers.py, llm.py | Средний |
| CORS `allow_origins=["*"]` | api.py | Низкий |
| Нет интеграционных тестов | tests/ | Средний |

---

## Участие в разработке

1. Fork → feature branch → PR
2. `pytest tests/` должен проходить перед PR
3. Новые провайдеры → `providers.py` + skill doc в `skills/`
4. Новые эндпоинты → схема в `src/models.py` сначала, маршрут в `api.py` последний
5. Обновляйте `CONTEXT_MAP.md` при добавлении файлов
