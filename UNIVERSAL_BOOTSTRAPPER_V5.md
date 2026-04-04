# 🚀 UNIVERSAL HIGH-LOAD PROJECT BOOTSTRAPPER v5

> **РОЛЬ:** Ты — Principal Architect, DevOps Lead & Security Engineer.
> **ЗАДАЧА:** Создать production-ready high-load проект с нуля: архитектура, код, безопасность, SEO, деплой, мониторинг, CI/CD.
> **СТЕК ПО УМОЛЧАНИЮ:** FastAPI + Python 3.11+ + PostgreSQL + Redis + Celery + Gunicorn + Docker + Kubernetes.
> **ПРИНЦИП:** "Engine + Modules + Infrastructure as Code".

---

## 📥 1. ВХОДНЫЕ ДАННЫЕ (Заполни перед запуском)

```
PROJECT_NAME: [Название]
SHORT_DESC: [Описание до 340 символов для GitHub]
DOMAIN: [Ниша: AI Tool, SaaS, E-commerce, API...]
KEY_FEATURES: [Список ключевых функций]
TARGET_AUDIENCE: [Кто пользователи]
EXPECTED_RPS: [Ожидаемая нагрузка: 100/1000/10000+]
KEYWORDS: [10-15 ключевых слов для SEO]
LANGUAGES: [EN, RU...]
BUDGET_MONTHLY: [Бюджет на инфраструктуру: $50/$200/$1000+]
```

---

## 🔍 2. АНАЛИЗ КОНТЕКСТА (Если есть файлы/архивы)

1. **Распаковка:** Извлеки все архивы, просканируй структуру.
2. **Дедупликация:** Удали дубликаты, temp-папки, кэш, `__pycache__`.
3. **Граф зависимостей:** Построй карту импортов, найди циклы.
4. **Самокритика:** Перед стартом выпиши риски:
   - Где могут быть утечки данных?
   - Что упадет под нагрузкой?
   - Есть ли спагетти-код (>500 строк в файле)?
   - Захардкожены ли секреты?
   - Совместимы ли версии библиотек?
   - Какие single points of failure?

---

## 🏗️ 3. АРХИТЕКТУРА HIGH-LOAD (Engine + Modules + Infra)

```text
[PROJECT_NAME]/
├── src/                          # МОДУЛИ (бизнес-логика)
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings (все env vars)
│   ├── models.py                 # Все Pydantic схемы
│   ├── database.py               # Async PostgreSQL (SQLAlchemy/asyncpg)
│   ├── cache.py                  # Redis client + caching decorators
│   ├── tasks.py                  # Celery tasks (async queue)
│   └── [domain_module].py        # Логика (каждый файл < 500 строк)
├── api.py                        # ДВИЖОК (FastAPI, Routes, Middleware)
├── providers.py                  # Внешние API адаптеры
├── gunicorn.conf.py              # Gunicorn конфиг (workers, threads)
├── celery_worker.py              # Celery worker entry point
├── landing.html                  # SEO Landing (EN)
├── landing_[LANG].html           # Локализации
├── requirements.txt              # Зависимости
├── pyproject.toml                # Ruff, pytest, packaging
├── .env.example                  # Шаблон (НИКАКИХ реальных ключей!)
├── .gitignore                    # Секреты, кэш, venv, data/
├── .dockerignore                 # Docker исключения
├── .editorconfig                 # Editor consistency
├── .pre-commit-config.yaml       # Pre-commit hooks (Ruff + compile)
├── Makefile                      # Dev-команды
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml            # Локальный стек (API + DB + Redis + Celery)
├── docker-compose.prod.yml       # Production стек (с мониторингом)
├── k8s/                          # Kubernetes манифесты
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml                  # Horizontal Pod Autoscaler
│   ├── configmap.yaml
│   └── secrets.yaml.example
├── nginx/
│   └── nginx.conf                # Reverse proxy + rate limiting
├── monitoring/
│   ├── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── alertmanager/
│       └── alertmanager.yml
├── README.md / README_[LANG].md
├── USAGE.md / USAGE_[LANG].md
├── AGENT.md                      # Контекст для AI-агентов
├── CONTEXT_MAP.md                # Карта системы
├── ROADMAP.md                    # План развития
├── CHANGELOG.md                  # История версий
├── SECURITY.md                   # Security policy
├── CODE_OF_CONDUCT.md            # Code of conduct
├── CHAT_HISTORY.md               # Лог сессии
├── robots.txt                    # SEO robots
├── sitemap.xml                   # SEO sitemap
└── .github/workflows/
    ├── ci.yml                    # Ruff + Pytest + Docker Build + Security Scan
    ├── cd.yml                    # Auto-deploy to staging/production
    └── security.yml              # Dependency audit + SAST
```

---

## 🛡️ 4. БЕЗОПАСНОСТЬ (CRITICAL — Production Grade)

### Реализуй в коде (`api.py`):

1. **API Key + JWT Auth:**
   - Публичные эндпоинты: GET /health, /status, /docs
   - Защищённые эндпоинты: требуют `X-API-Key` или `Authorization: Bearer <JWT>`
   - API ключи хранятся в PostgreSQL (хэш bcrypt), не в env vars
   - JWT tokens с expiry (access: 15min, refresh: 7d)

2. **Rate Limiter (Redis-backed):**
   - Sliding window algorithm через Redis
   - Разные лимиты для разных эндпоинтов:
     - `/scrape`: 30 req/min
     - `/synthesize`: 5 req/min
     - `/screenshot`: 10 req/min
   - Ответ: `429 Too Many Requests` + `Retry-After` header

3. **CORS:**
   - Strict: `allow_origins=["https://yourdomain.com"]` (через env var)
   - No wildcards in production

4. **Валидация:** Pydantic схемы на ВСЕХ входах. Никаких `dict` напрямую.

5. **Global Exception Handler:**
   ```python
   @app.exception_handler(Exception)
   async def global_handler(request, exc):
       logger.error(f"Unhandled: {exc}", exc_info=True, extra={"path": request.url.path})
       return JSONResponse(500, {"detail": "Internal server error"})
   ```

6. **Security Headers (middleware):**
   ```python
   app.add_middleware(
       TrustedHostMiddleware,
       allowed_hosts=["yourdomain.com", "api.yourdomain.com"]
   )
   # Headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection,
   # Strict-Transport-Security, Content-Security-Policy
   ```

7. **SQL Injection Prevention:**
   - Только ORM (SQLAlchemy async) или параметризованные запросы
   - Никаких f-strings в SQL

8. **Secrets Management:**
   - В production: HashiCorp Vault / AWS Secrets Manager / Kubernetes Secrets
   - В .env.example: только заглушки
   - Никогда не логируй секреты

9. **Input Sanitization:**
   - URL validation (allowlist схем: http, https)
   - File upload size limits
   - XSS prevention в ответах

### Инструкция для пользователя (в README):

```markdown
## 🔒 Security Checklist
- [ ] Никогда не коммить `.env` файл
- [ ] Ротация API_KEY каждые 30 дней
- [ ] Для публичного фронта используй отдельный Read-Only ключ
- [ ] Включи Rate Limiting на продакшене
- [ ] Настрой CORS под свой домен
- [ ] Используй HTTPS (Let's Encrypt / Cloudflare)
- [ ] Включи WAF (Cloudflare / AWS WAF)
- [ ] Настрой alerting на аномалии (Prometheus + Alertmanager)
- [ ] Регулярно обновляй зависимости (`pip audit`)
- [ ] Проводи пентесты раз в квартал
```

---

## 🌐 5. SEO ЛЕНДИНГ (2026 Standard — JSON-LD Only)

### Обязательные JSON-LD схемы (в `<head>` каждой страницы):

#### 5.1. WebApplication + Organization
```json
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "[PROJECT_NAME]",
  "description": "[SHORT_DESC]",
  "url": "https://[DOMAIN].com/",
  "applicationCategory": "[CATEGORY]",
  "operatingSystem": "Any",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "featureList": ["[FEATURE_1]", "[FEATURE_2]", "[FEATURE_3]"],
  "author": {
    "@type": "Organization",
    "name": "[ORG_NAME]",
    "url": "https://[DOMAIN].com/",
    "sameAs": [
      "https://github.com/[USER]/[REPO]",
      "https://twitter.com/[HANDLE]"
    ]
  }
}
```

#### 5.2. WebSite + SearchAction
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "[PROJECT_NAME]",
  "url": "https://[DOMAIN].com/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://[DOMAIN].com/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
```

#### 5.3. FAQPage (для rich snippets в Google)
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[Question 1]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Answer 1]"
      }
    }
  ]
}
```

#### 5.4. HowTo (если есть пошаговый гайд на лендинге)
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to use [PROJECT_NAME]",
  "description": "Step-by-step guide to get started",
  "step": [
    {
      "@type": "HowToStep",
      "position": 1,
      "name": "Install",
      "text": "Clone the repo and install dependencies"
    }
  ]
}
```

#### 5.5. BreadcrumbList
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://[DOMAIN].com/"
    }
  ]
}
```

#### 5.6. SoftwareApplication (для Google Discover)
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "[PROJECT_NAME]",
  "operatingSystem": "Web",
  "applicationCategory": "DeveloperApplication",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "127"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
```

### Обязательные мета-теги:

```html
<!-- Core SEO -->
<title>[PROJECT_NAME] — [KEYWORD_RICH_DESCRIPTION]</title>
<meta name="description" content="[150-160 символов с ключами]">
<meta name="keywords" content="[10-15 ключевых слов]">
<link rel="canonical" href="https://[DOMAIN].com/">
<meta name="robots" content="index, follow">
<meta name="author" content="[ORG_NAME]">
<meta name="publisher" content="[ORG_NAME]">
<link rel="alternate" hreflang="en" href="https://[DOMAIN].com/landing.html">
<link rel="alternate" hreflang="ru" href="https://[DOMAIN].com/landing_ru.html">
<link rel="alternate" hreflang="x-default" href="https://[DOMAIN].com/landing.html">

<!-- Open Graph -->
<meta property="og:title" content="[PROJECT_NAME] — [DESC]">
<meta property="og:description" content="[DESC]">
<meta property="og:type" content="website">
<meta property="og:url" content="https://[DOMAIN].com/">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="ru_RU">
<meta property="og:site_name" content="[PROJECT_NAME]">
<meta property="og:image" content="https://[DOMAIN].com/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@[HANDLE]">
<meta name="twitter:title" content="[PROJECT_NAME]">
<meta name="twitter:description" content="[DESC]">
<meta name="twitter:image" content="https://[DOMAIN].com/og-image.png">

<!-- Favicon (inline SVG) -->
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

### Структура лендинга (контент-блоки):

1. **Hero:** H1 с ключом, подзаголовок, CTA-кнопка
2. **Status Bar:** API/DB/Cache статус (зеленые точки)
3. **Tool/Interactive:** Форма ввода → результат (основная функция)
4. **Features Grid:** 6 карточек с ключевыми возможностями
5. **Text Block (SEO):** 300-500 слов с ключами, сущностями, намерением пользователя
6. **How To:** 3-4 шага (с JSON-LD HowTo)
7. **Stats/Social Proof:** "10,000+ API calls/day", "99.9% uptime"
8. **FAQ:** 5-7 вопросов (с JSON-LD FAQPage)
9. **Footer:** Копирайт, GitHub, Terms, Privacy, Analytics

### Legal:
```html
<footer>
  <p>&copy; 2026 [PROJECT_NAME]. All rights reserved.</p>
  <a href="#terms">Terms of Service</a> |
  <a href="#privacy">Privacy Policy</a> |
  <a href="https://github.com/[USER]/[REPO]" rel="noopener noreferrer">GitHub</a>
</footer>
```

### Аналитика (Privacy-First):
```html
<!-- Plausible (recommended, GDPR-compliant) -->
<script defer data-domain="[DOMAIN].com" src="https://plausible.io/js/script.js"></script>

<!-- OR Umami self-hosted -->
<script defer src="https://umami.[DOMAIN].com/script.js" data-website-id="[UUID]"></script>
```

---

## ☁️ 6. ДЕПЛОЙ HIGH-LOAD (Best Options April 2026)

### 6.1. Рекомендуемый стек для High-Load

```
┌─────────────────────────────────────────────────────────────┐
│  CDN: Cloudflare (Free/Pro $20/mo)                         │
│  ├── DDoS protection                                       │
│  ├── WAF (Web Application Firewall)                        │
│  ├── Cache static assets (landing, images)                 │
│  └── SSL/TLS termination                                   │
├─────────────────────────────────────────────────────────────┤
│  Frontend: Cloudflare Pages / GitHub Pages (Free)          │
│  └── Static HTML, global CDN, < 50ms TTFB                  │
├─────────────────────────────────────────────────────────────┤
│  API: Kubernetes Cluster                                   │
│  ├── Managed K8s: DigitalOcean ($12/mo control plane)      │
│  │   OR Hetzner Cloud (self-managed, ~$15/mo)              │
│  │   OR AWS EKS ($73/mo control plane)                     │
│  ├── Gunicorn + Uvicorn workers (4-16 workers)             │
│  ├── Horizontal Pod Autoscaler (1-20 pods)                 │
│  └── Ingress: Nginx / Traefik                              │
├─────────────────────────────────────────────────────────────┤
│  Database: Managed PostgreSQL                              │
│  ├── DigitalOcean Managed PG ($15/mo basic)                │
│  ├── AWS RDS PostgreSQL ($15/mo db.t4g.micro)              │
│  ├── Supabase (Free tier, $25/mo Pro)                      │
│  └── Neon (Serverless PG, Free tier)                       │
├─────────────────────────────────────────────────────────────┤
│  Cache: Managed Redis                                      │
│  ├── DigitalOcean Managed Redis ($15/mo)                   │
│  ├── Upstash (Serverless Redis, Free tier)                 │
│  └── AWS ElastiCache ($14/mo cache.t4g.micro)              │
├─────────────────────────────────────────────────────────────┤
│  Queue: Celery + RabbitMQ / Redis                          │
│  ├── RabbitMQ (CloudAMQP Free tier)                        │
│  └── Redis Streams (встроенный в Redis)                    │
├─────────────────────────────────────────────────────────────┤
│  Monitoring:                                               │
│  ├── Prometheus + Grafana (self-hosted, Free)              │
│  ├── Sentry (Error tracking, Free 5K events/mo)            │
│  ├── UptimeRobot (Uptime monitoring, Free 50 monitors)     │
│  └── Logtail / Loki (Log aggregation)                      │
├─────────────────────────────────────────────────────────────┤
│  CI/CD: GitHub Actions                                     │
│  ├── ci.yml: Lint + Test + Security Scan + Docker Build    │
│  ├── cd.yml: Auto-deploy to staging → production           │
│  └── security.yml: Dependabot + pip audit + SAST           │
└─────────────────────────────────────────────────────────────┘
```

### 6.2. Сравнение хостингов (Апрель 2026)

#### API Backend

| Платформа | Цена/мес | CPU | RAM | Масштабирование | Лучше для |
|-----------|----------|-----|-----|-----------------|-----------|
| **Hetzner Cloud** | $5-50 | 1-8 vCPU | 2-32GB | Manual (Terraform) | 💰 Лучшая цена/качество |
| **DigitalOcean** | $6-48 | 1-4 vCPU | 1-8GB | Manual + K8s ($12/mo) | 🟢 Простота + K8s |
| **Render** | Free-$45 | Shared | 512MB-2GB | Auto (paid only) | 🚀 Быстрый старт |
| **Railway** | $5 кредит | Shared | 512MB | Auto | 🛤 Прототипы |
| **Fly.io** | Free-$$ | 1-4 vCPU | 256MB-2GB | Auto | 🌍 Global edge |
| **AWS ECS** | $15+ | 1-4 vCPU | 1-8GB | Auto | 🏢 Enterprise |
| **AWS EKS** | $73+ | Auto | Auto | Auto | 🏢 Large scale |
| **GCP Cloud Run** | Pay-per-use | Auto | Auto | Auto | ⚡ Serverless |
| **Vultr** | $6-48 | 1-4 vCPU | 1-8GB | Manual | 💰 Альтернатива DO |

#### Database

| Платформа | Цена/мес | Storage | HA | Лучше для |
|-----------|----------|---------|----|-----------|
| **Neon** | Free-$25 | 1-100GB | No/Yes | 🟢 Serverless PG |
| **Supabase** | Free-$25 | 0.5-100GB | No/Yes | 🟢 PG + Auth + Storage |
| **DigitalOcean PG** | $15-100 | 10-614GB | Yes | 🟢 Managed PG |
| **AWS RDS** | $15-100+ | 20GB+ | Yes | 🏢 Enterprise |
| **Self-hosted (Hetzner)** | $5 | Unlimited | Manual | 💰 Дёшево, но сам админь |

#### GPU (для Ollama/VLM)

| Платформа | GPU | Цена/час | Цена/мес | Лучше для |
|-----------|-----|----------|----------|-----------|
| **RunPod** | RTX 4090 | $0.44 | ~$320 | 🟢 Лучший price/performance |
| **Vast.ai** | RTX 4090 | $0.20-0.40 | ~$150-300 | 💰 Самый дешёвый |
| **Lambda Labs** | A10 | $0.60 | ~$430 | ⚡ Быстрый деплой |
| **AWS g5.xlarge** | A10G | $1.01 | ~$730 | 🏢 Enterprise |
| **Vultr GPU** | A100 | $1.40 | ~$1000 | 🏢 Enterprise |
| **Self-hosted** | RTX 4090 | $0 | ~$1600 (hardware) | 💰 Долгосрочно |

#### CDN + WAF

| Платформа | Цена/мес | WAF | DDoS | Лучше для |
|-----------|----------|-----|------|-----------|
| **Cloudflare Free** | $0 | Basic | Basic | 🟢 Лучший бесплатный |
| **Cloudflare Pro** | $20 | Advanced | Advanced | 🟢 Лучший overall |
| **Cloudflare Business** | $200 | Enterprise | Enterprise | 🏢 Enterprise |

### 6.3. Рекомендуемые конфигурации по бюджету

#### Бюджет $50/мес (Small Production)
```
API: Hetzner CPX21 (2 vCPU, 4GB RAM) — $7/mo
DB: Neon Free tier — $0/mo
Cache: Upstash Free tier — $0/mo
CDN: Cloudflare Free — $0/mo
Frontend: GitHub Pages — $0/mo
Monitoring: UptimeRobot Free + Sentry Free — $0/mo
GPU: OpenRouter API (pay-per-use) — ~$20/mo
Итого: ~$27/mo (остаток на трафик)
```

#### Бюджет $200/мес (Medium Production)
```
API: Hetzner CCX22 (4 vCPU, 16GB RAM) — $25/mo
DB: DigitalOcean Managed PG (Basic) — $15/mo
Cache: DigitalOcean Managed Redis — $15/mo
CDN: Cloudflare Pro — $20/mo
Frontend: Cloudflare Pages — $0/mo
Monitoring: Grafana Cloud Free + Sentry Pro — $29/mo
GPU: RunPod RTX 4090 (part-time) — ~$50/mo
Queue: RabbitMQ (CloudAMqp Little Lemur) — $0/mo
Итого: ~$154/mo (остаток на трафик)
```

#### Бюджет $1000/мес (High-Load Production)
```
API: Kubernetes (Hetzner 3x CCX32) — $90/mo
DB: DigitalOcean Managed PG (Pro, HA) — $60/mo
Cache: DigitalOcean Managed Redis (HA) — $60/mo
CDN: Cloudflare Pro — $20/mo
Frontend: Cloudflare Pages Pro — $0/mo
Monitoring: Grafana Cloud + Sentry + Logtail — $100/mo
GPU: RunPod 2x RTX 4090 (always-on) — $640/mo
Queue: RabbitMQ (CloudAMQP Regular) — $20/mo
Backups: S3-compatible (Backblaze B2) — $10/mo
Итого: ~$1000/mo
```

### 6.4. Docker Compose (Production)

```yaml
version: "3.8"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8100
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build: .
    command: celery -A src.tasks worker -l info -c 4
    env_file: .env
    depends_on: [postgres, redis, rabbitmq]
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: scraping
      POSTGRES_USER: scraping
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmqdata:/var/lib/rabbitmq
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on: [api]
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - promdata:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafanadata:/var/lib/grafana
    depends_on: [prometheus]
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
  rabbitmqdata:
  promdata:
  grafanadata:
```

### 6.5. Gunicorn Config (`gunicorn.conf.py`)

```python
import multiprocessing

# Workers: 2-4 per CPU core
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Graceful shutdown
graceful_timeout = 30
```

---

## 🧪 7. ТЕСТИРОВАНИЕ И КАЧЕСТВО КОДА

### 7.1. Структура тестов
```
tests/
├── conftest.py           # Фикстуры, моки, тестовая БД (PostgreSQL test container)
├── test_api.py           # Интеграционные тесты (TestClient)
├── test_security.py      # Тесты защиты (API Key, Rate Limit, JWT)
├── test_[module].py      # Unit-тесты модулей
├── test_tasks.py         # Celery task tests
└── load_test.py          # Locust load tests
```

### 7.2. Load Testing (Locust)
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def scrape(self):
        self.client.post("/scrape", json={"url": "https://example.com"})

    @task(1)
    def status(self):
        self.client.get("/status")
```

### 7.3. Чек-лист качества кода
- [ ] ❌ Нет циклических импортов
- [ ] ❌ Нет файлов > 500 строк
- [ ] ❌ Нет глобальных переменных
- [ ] ❌ Нет захардкоженных секретов
- [ ] ❌ Нет SQL injection (только ORM)
- [ ] ✅ Все `.py` проходят `python -m py_compile`
- [ ] ✅ Ruff lint без ошибок
- [ ] ✅ Тесты в `tests/`
- [ ] ✅ Load test проходит (1000 RPS без ошибок)
- [ ] ✅ Security scan чист (`pip audit`, `bandit`)
- [ ] ✅ Health check endpoint работает
- [ ] ✅ Graceful shutdown работает

---

## 📊 8. МОНИТОРИНГ И ALERTING

### 8.1. Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration")

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(time.time() - start)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 8.2. Alertmanager Rules
```yaml
groups:
  - name: critical
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.endpoint }}"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
```

---

## 📝 9. ДОКУМЕНТАЦИЯ

### 9.1. README.md (EN)
- Описание проекта (с ключами)
- Архитектура (ASCII-диаграмма)
- Quick Start (3 шага)
- API Endpoints (таблица)
- Deploy Guide (с ценами)
- Links: USAGE, CONTEXT_MAP, AGENT, ROADMAP

### 9.2. README_[LANG].md
- Полный перевод README
- Ссылка на EN-версию

### 9.3. USAGE.md / USAGE_[LANG].md
- Полное руководство: конфиг, запуск, примеры curl, Python API, Docker, дебаггинг, FAQ

### 9.4. AGENT.md
- Контекст для AI: структура файлов, правила архитектуры, известные техдолги, паттерны

### 9.5. CONTEXT_MAP.md
- Визуальная карта системы, потоки данных, зависимости модулей, API Map, типы данных

### 9.6. ROADMAP.md
- Что сделано (✅), в процессе (🔄), планируется (📋), идеи (💡)
- Tech Debt Tracker

### 9.7. CHANGELOG.md
- История версий по [Keep a Changelog](https://keepachangelog.com/)

### 9.8. CHAT_HISTORY.md
- Лог сессии разработки. Обновляй при каждом крупном изменении.

---

## 🚀 10. ФИНАЛИЗАЦИЯ

### 10.1. Git команды
```bash
git init
git add .
git commit -m "Initial commit: [PROJECT_NAME] — [DESC]"
git branch -M main
git remote add origin https://github.com/[USER]/[REPO].git
git push -u origin main
```

### 10.2. Финальный чек-лист (ПЕРЕД выдачей результата)
- [ ] Секреты не захардкожены?
- [ ] Защита (API Key + Rate Limit + JWT) работает?
- [ ] CORS настроен строго?
- [ ] Инструкции по деплою полные (с ценами)?
- [ ] Тесты в `tests/`?
- [ ] Load test написан?
- [ ] Нет дубликатов файлов?
- [ ] Все `.py` прошли `py_compile`?
- [ ] JSON-LD валиден?
- [ ] hreflang теги есть?
- [ ] Canonical URL указан?
- [ ] Legal (Terms/Privacy) добавлены?
- [ ] Аналитика подключена?
- [ ] Фавикон есть?
- [ ] Лендинг адаптивный (mobile-first)?
- [ ] robots.txt и sitemap.xml есть?
- [ ] .dockerignore есть?
- [ ] .editorconfig есть?
- [ ] Pre-commit hooks настроены?
- [ ] Graceful shutdown работает?
- [ ] Health check endpoint есть?
- [ ] Prometheus metrics есть?
- [ ] CI/CD pipeline настроен?
- [ ] Security scan чист?

### 10.3. Вывод
Выдай:
1. Структуру проекта
2. Код файлов (группируя по смыслу)
3. Финальный чек-лист
4. Инструкцию по деплою (с ценами)
5. Инструкцию по мониторингу
6. Ссылку на CHAT_HISTORY.md

---

> **ПРИМЕЧАНИЕ:** Этот шаблон адаптируется под любой high-load проект. Укажи `[PROJECT_NAME]`, `[DESC]`, `[KEYWORDS]`, `[EXPECTED_RPS]`, `[BUDGET_MONTHLY]` — и я разверну всё автоматически.

---

## Что нового в v5 (по сравнению с v4):

- ✅ High-Load архитектура: PostgreSQL, Redis, Celery, Gunicorn, K8s
- ✅ Сравнение 30+ хостингов (Апрель 2026): Hetzner, DO, AWS, GCP, RunPod, Vast.ai, Vultr
- ✅ 3 конфигурации по бюджету: $50, $200, $1000/мес
- ✅ Docker Compose Production (с мониторингом)
- ✅ Gunicorn конфиг (workers, threads, graceful timeout)
- ✅ Kubernetes манифесты (deployment, service, ingress, HPA)
- ✅ Nginx reverse proxy + rate limiting
- ✅ Prometheus + Grafana мониторинг
- ✅ Alertmanager правила (error rate, latency, downtime)
- ✅ Locust load testing
- ✅ JWT auth + API key management (PostgreSQL-backed)
- ✅ Redis-backed sliding window rate limiter
- ✅ Security Headers (HSTS, CSP, X-Frame-Options)
- ✅ SQL injection prevention (ORM only)
- ✅ Secrets management (Vault/AWS SM/K8s Secrets)
- ✅ Input sanitization (URL validation, file size limits)
- ✅ CI/CD: ci.yml + cd.yml + security.yml
- ✅ Health check + graceful shutdown
- ✅ Pagination enforcement (max 200 per request)
- ✅ robots.txt + sitemap.xml
- ✅ .dockerignore + .editorconfig + pre-commit
- ✅ CHANGELOG.md + SECURITY.md + CODE_OF_CONDUCT.md
- ✅ SoftwareApplication Schema (для Google Discover)
- ✅ hreflang x-default
- ✅ OG image dimensions
- ✅ Publisher meta tag
- ✅ Social proof блок на лендинге
- ✅ Uptime monitoring (UptimeRobot)
- ✅ Error tracking (Sentry)
- ✅ Log aggregation (Loki/Logtail)
