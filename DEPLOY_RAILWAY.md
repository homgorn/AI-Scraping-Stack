# DEPLOY_RAILWAY.md — Деплой на Railway

> Бэкенд (FastAPI API) → Railway.app
> Фронтенд (landing.html) → любой статический хостинг

---

## Что такое Railway

Railway — PaaS-платформа для деплоя приложений. Бесплатный план: $5 кредитов/мес. Поддерживает Docker, Python, Node.js.

---

## Шаг 1: Подготовка репозитория

```bash
# Убедитесь что проект в git
cd scrapling
git init
git add .
git commit -m "Initial commit: AI Scraping Stack v0.3.1"

# Создайте репозиторий на GitHub
gh repo create ai-scraping-stack --public --source=. --remote=origin
git push -u origin main
```

---

## Шаг 2: Создайте проект на Railway

1. Откройте https://railway.app/
2. Войдите через GitHub
3. Нажмите **New Project** → **Deploy from GitHub repo**
4. Выберите репозиторий `ai-scraping-stack`

---

## Шаг 3: Настройте переменные окружения

В панели Railway → **Variables**:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
JINA_API_KEY=jina_...
FIRECRAWL_API_KEY=fc-...
SCRAPINGDOG_KEY=...
SCRAPERAPI_KEY=...
ZENROWS_KEY=...
PROXY_URL=
DB_PATH=/app/data/scrapling.db
MODEL_REGISTRY_PATH=/app/data/models.json
SCREENSHOTS_DIR=/app/data/screenshots
```

> **Важно:** Railway не поддерживает Ollama напрямую (нужен GPU). Для production используйте только OpenRouter. Если нужен Ollama — используйте Timeweb с GPU (см. DEPLOY_TIMEWEB.md).

---

## Шаг 4: Настройте Docker

Railway автоматически обнаружит `Dockerfile`. Убедитесь что он работает:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] httpx pydantic pydantic-settings python-dotenv \
    scrapling ollama openai
COPY . .
RUN scrapling install
EXPOSE 8100
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8100"]
```

---

## Шаг 5: Настройте порты и домен

1. В Railway → **Settings** → **Networking**
2. Добавьте **Public Networking** на порт `8100`
3. Railway выдаст URL вида: `https://your-project.railway.app`
4. Опционально: привяжите свой домен

---

## Шаг 6: Обновите API_URL в landing.html

Откройте `landing.html` и замените:

```javascript
const API_URL = 'https://your-project.railway.app';
```

Задеплойте landing.html на любой статический хостинг (GitHub Pages, Netlify, Vercel, Timeweb).

---

## Шаг 7: Настройте persistent storage

Railway удаляет файловую систему при каждом деплое. Для сохранения данных:

1. Railway → **Plugins** → **Add Plugin** → **PostgreSQL** или **Redis**
2. Либо используйте Railway Volumes:
   - Settings → **Volumes** → Add Volume → `/app/data`

---

## Проверка

```bash
# Проверьте что API работает
curl https://your-project.railway.app/
# → {"status":"ok","version":"1.0.0","docs":"/docs"}

# Проверьте статус
curl https://your-project.railway.app/status
```

---

## Стоимость

| Ресурс | Бесплатно | Платно |
|--------|-----------|--------|
| Compute | $5 кредитов/мес | $0.000231/GB-час |
| Storage | 500MB | $0.25/GB-мес |
| Bandwidth | Без лимита | Без лимита |

**Итого:** ~$0-5/мес в зависимости от нагрузки.

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| Build failed | Проверьте Dockerfile, убедитесь что `requirements.txt` корректен |
| App crashed | Проверьте логи в Railway → Deployments → Logs |
| Ollama не работает | Railway не поддерживает Ollama. Используйте только OpenRouter |
| DB не сохраняется | Настройте Volume или используйте внешнюю БД |
| Timeout на scrape | Увеличьте timeout в Railway Settings → **Healthcheck** |

---

## CI/CD (автоматический деплой)

Railway автоматически деплоит при push в main. Для ручного триггера:

```bash
railway up
```

Или через GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/cli@v1
        with:
          args: up --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```
