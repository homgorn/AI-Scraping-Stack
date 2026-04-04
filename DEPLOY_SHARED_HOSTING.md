# DEPLOY_SHARED_HOSTING.md — Деплой фронтенда на виртуальный хостинг

> landing.html → любой shared hosting (Timeweb, Beget, Reg.ru, Hostinger)
> Бэкенд → отдельно на Railway/Timeweb Cloud

---

## Архитектура

```
┌─────────────────────────────┐     fetch()      ┌──────────────────┐
│ Shared Hosting (фронтенд)   │ ───────────────→  │ Бэкенд API       │
│ landing.html + CSS + JS     │   POST /scrape    │ (Railway/Timeweb)│
│ SEO мета + Schema.org       │   POST /synthesize│                  │
│                             │ ←───────────────  │                  │
└─────────────────────────────┘     JSON          └──────────────────┘
```

---

## Шаг 1: Настройте API_URL

Откройте `landing.html` и найдите строку:

```javascript
const API_URL = 'http://localhost:8100';
```

Замените на URL вашего бэкенда:

```javascript
// Railway
const API_URL = 'https://your-project.railway.app';

// Timeweb Cloud
const API_URL = 'https://api.ваш-домен.com';

// Timeweb Cloud + Nginx прокси
const API_URL = 'https://ваш-домен.com/api';
```

---

## Шаг 2: Настройте CORS на бэкенде

Убедитесь что `api.py` разрешает запросы с вашего домена:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ваш-домен.com", "http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Или для разработки оставьте `["*"]`.

---

## Шаг 3: Загрузите на хостинг

### Timeweb Hosting

1. Панель → **Файловый менеджер** → `public_html/`
2. Загрузите `landing.html`
3. Переименуйте в `index.html` (если нужно)

### Beget

1. Панель → **Файловый менеджер** → `public_html/`
2. Загрузите `landing.html` как `index.html`

### Hostinger

1. hPanel → **File Manager** → `public_html/`
2. Загрузите `landing.html` как `index.html`

### Через FTP (FileZilla)

1. Подключитесь к FTP (хост, логин, пароль из панели хостинга)
2. Перейдите в `public_html/`
3. Перетащите `landing.html` → переименуйте в `index.html`

---

## Шаг 4: Привяжите домен

1. В панели хостинга → **Домены** → **Добавить домен**
2. Укажите ваш домен
3. Настройте DNS у регистратора:
   ```
   A record: ваш-домен.com → IP хостинга
   CNAME: www → ваш-домен.com
   ```

---

## Шаг 5: Включите HTTPS

Большинство хостингов предоставляют бесплатный SSL (Let's Encrypt):

1. Панель → **SSL** → **Let's Encrypt** → **Установить**
2. Подождите 5-15 минут

---

## SEO-оптимизация (уже встроена в landing.html)

### Что уже есть:

- ✅ `<title>` с ключевыми словами
- ✅ `<meta description>` — описание для поисковиков
- ✅ `<meta keywords>` — ключевые слова
- ✅ Open Graph мета — для соцсетей
- ✅ Twitter Card — для Twitter/X
- ✅ Schema.org JSON-LD — SoftwareApplication, WebSite, FAQPage
- ✅ Semantic HTML5 — `<header>`, `<main>`, `<section>`, `<article>`, `<footer>`
- ✅ `<link rel="canonical">` — предотвращает дубли
- ✅ `<meta name="robots" content="index, follow">` — индексация
- ✅ FAQ секция с `<details>` — rich snippets в Google
- ✅ Mobile responsive — адаптивный дизайн
- ✅ Быстрая загрузка — нет внешних зависимостей, inline CSS/JS

### Ключевые слова для SEO:

```
AI скрапинг, анализ конкурентов, генерация сайтов, веб-разведка,
парсинг сайтов, визуальный аудит, искусственный интеллект,
scraping, competitor analysis, AI website generator,
VLM анализ, мультискрапинг, дизайн-аудит
```

### Что можно улучшить:

1. **Добавьте robots.txt:**
   ```
   User-agent: *
   Allow: /
   Sitemap: https://ваш-домен.com/sitemap.xml
   ```

2. **Создайте sitemap.xml:**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     <url>
       <loc>https://ваш-домен.com/</loc>
       <lastmod>2026-04-04</lastmod>
       <changefreq>weekly</changefreq>
       <priority>1.0</priority>
     </url>
   </urlset>
   ```

3. **Зарегистрируйте в Google Search Console:**
   - https://search.google.com/search-console
   - Добавьте сайт, подтвердите владение
   - Отправьте sitemap.xml

4. **Зарегистрируйте в Яндекс.Вебмастер:**
   - https://webmaster.yandex.ru/
   - Добавьте сайт, подтвердите владение
   - Отправьте sitemap.xml

5. **Добавьте контент:**
   - Блог-секция с кейсами использования
   - Примеры результатов анализа
   - Отзывы/тестимониалы

---

## Проверка

```bash
# Проверьте что страница доступна
curl https://ваш-домен.com/

# Проверьте SEO мета
curl -s https://ваш-домен.com/ | grep -i "<title>"
curl -s https://ваш-домен.com/ | grep -i "meta description"
curl -s https://ваш-домен.com/ | grep -i "schema.org"

# Проверьте API связь
# Откройте https://ваш-домен.com/ в браузере
# Введите URL → нажмите "Анализировать"
```

---

## Стоимость shared hosting

| Хостинг | Цена/мес | SSD | Трафик |
|---------|----------|-----|--------|
| Timeweb | ~200₽ | 5GB | Безлимит |
| Beget | ~220₽ | 5GB | Безлимит |
| Reg.ru | ~150₽ | 3GB | Безлимит |
| Hostinger | ~100₽ | 10GB | Безлимит |

**Итого:** ~100-220₽/мес за фронтенд.

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| CORS error | Добавьте домен в `allow_origins` на бэкенде |
| Страница не грузится | Убедитесь что файл называется `index.html` |
| API не отвечает | Проверьте URL бэкенда, CORS, firewall |
| SSL не работает | Подождите 15 мин после установки Let's Encrypt |
| Медленная загрузка | Сожмите HTML, включите gzip в .htaccess |
