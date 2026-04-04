# Деплой

> Пошаговые инструкции по деплою AI Scraping Stack на различные платформы.

## Обзор

AI Scraping Stack состоит из двух частей, которые можно деплоить отдельно:

```
┌─────────────────────┐     fetch()      ┌──────────────────┐
│ Фронтенд (Статика)  │ ───────────────→  │ Бэкенд (API)     │
│ landing.html        │   POST /scrape    │ FastAPI (Python) │
│ GitHub Pages / CF   │   POST /synthesize│ Render / Railway │
└─────────────────────┘ ←────────────────┘                  │
                     JSON ответ            └──────────────────┘
```

---

## Деплой бэкенда

### Вариант 1: Render.com (Бесплатно)

**Лучше всего для:** Быстрый деплой, без привязки карты.

1. Зайдите на [render.com](https://render.com) → Sign Up через GitHub
2. Нажмите **New +** → **Web Service**
3. Выберите репо `ai-scraping-stack`
4. Заполните:
   - **Name:** `ai-scraping-stack`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** **Free**
5. Добавьте переменные окружения:
   - `OPENROUTER_API_KEY=sk-or-v1-...`
   - `API_KEY=ваш-секретный-ключ` (для защиты)
   - Другие ключи из `.env.example`
6. Нажмите **Create Web Service**

API будет доступен по адресу: `https://ai-scraping-stack.onrender.com`

**Примечание:** Бесплатный тариф засыпает через 15 минут без активности. Используйте `keep-alive.yml` GitHub Action для пинга каждые 10 минут.

### Вариант 2: Railway.app

**Лучше всего для:** Больше ресурсов, $5 бесплатных кредитов/мес.

1. Зайдите на [railway.app](https://railway.app) → Sign Up через GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Выберите `ai-scraping-stack`
4. Добавьте переменные окружения в панели Railway
5. Railway автоматически обнаружит `Dockerfile` и соберёт образ

### Вариант 3: Timeweb Cloud (с GPU для Ollama)

**Лучше всего для:** Полный контроль, локальные ИИ-модели, российский хостинг.

Смотрите [DEPLOY_TIMEWEB.md](../DEPLOY_TIMEWEB.md) для подробных инструкций, включая:
- Настройку GPU сервера
- Установку Ollama
- Nginx обратный прокси
- systemd сервис
- SSL через Let's Encrypt

### Вариант 4: Docker

```bash
# Сборка
docker build -t ai-scraping-stack .

# Запуск
docker run -p 8100:8100 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e API_KEY=ваш-секретный-ключ \
  ai-scraping-stack

# Или через docker-compose
docker-compose up -d
```

---

## Деплой фронтенда

### Вариант 1: GitHub Pages (Бесплатно)

1. Зайдите в **Settings** репозитория → **Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `main`, папка: `/ (root)`
4. Сайт будет по адресу: `https://homgorn.github.io/ai-scraping-stack/landing.html`

### Вариант 2: Cloudflare Pages (Бесплатно)

1. Зайдите на [pages.cloudflare.com](https://pages.cloudflare.com)
2. Подключите GitHub репо
3. Настройки сборки: не нужны (статический HTML)
4. Деплой

### Вариант 3: Netlify (Бесплатно)

1. Перетащите папку на [app.netlify.com/drop](https://app.netlify.com/drop)
2. Или подключите GitHub репо

---

## Настройка после деплоя

### 1. Обновите API_URL в landing.html

Откройте `landing.html` и установите:
```javascript
const API_URL = 'https://your-api.onrender.com';
const API_KEY = 'ваш-секретный-ключ'; // Тот же, что в Render
```

### 2. Добавьте GitHub Secret для Keep-Alive

1. **Settings** репозитория → **Secrets and variables** → **Actions**
2. **New repository secret**
3. **Name:** `RENDER_API_URL`
4. **Value:** `https://your-api.onrender.com`

### 3. Установите переменные окружения в Render

| Переменная | Пример | Обязательна |
|------------|--------|-------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | Для облачных LLM |
| `API_KEY` | `MySecret_2026!` | Для защиты API |
| `JINA_API_KEY` | `jina_...` | Для высокого лимита |
| `OLLAMA_HOST` | `http://localhost:11434` | Только если Ollama запущен |
| `DB_PATH` | `/app/data/scrapling.db` | Для постоянного хранения |

---

## Чек-лист безопасности

- [ ] `API_KEY` установлен в переменных Render
- [ ] `API_KEY` установлен в `landing.html` (то же значение)
- [ ] CORS ограничен вашим доменом (не `*`)
- [ ] HTTPS включён (автоматически на Render/GitHub Pages)
- [ ] Файл `.env` НЕ закоммичен в git
- [ ] Rate limiting включён (по умолчанию: 10 запр/мин)
- [ ] Keep-alive workflow настроен

## Мониторинг

- **Логи Render:** Dashboard → ваш сервис → вкладка **Logs**
- **GitHub Actions:** Вкладка Actions → запуски `keep-alive`
- **Здоровье API:** Эндпоинт `GET /status`
- **Аналитика:** Скрипт Plausible/Umami в `landing.html`
