# DEPLOY_TIMEWEB.md — Деплой на Timeweb Cloud

> Бэкенд + Ollama (с GPU) → Timeweb Cloud
> Фронтенд (landing.html) → тот же сервер через Nginx

---

## Что такое Timeweb Cloud

Timeweb Cloud — российский облачный провайдер. Виртуальные серверы с GPU (NVIDIA), SSD, безлимитный трафик. От 500₽/мес.

---

## Шаг 1: Создайте сервер

1. Откройте https://timeweb.cloud/
2. **Виртуальные серверы** → **Создать сервер**
3. Конфигурация:
   - **OS:** Ubuntu 22.04
   - **CPU:** 4+ vCPU
   - **RAM:** 8+ GB
   - **GPU:** NVIDIA (для Ollama) — обязательно если нужен локальный ИИ
   - **Disk:** 40+ GB SSD
   - **Region:** Москва (ru-1)

---

## Шаг 2: Подключитесь к серверу

```bash
ssh root@ВАШ_IP
```

---

## Шаг 3: Установите зависимости

```bash
# Обновите систему
apt update && apt upgrade -y

# Python 3.11+
apt install -y python3.11 python3.11-venv python3-pip git curl

# Docker (опционально)
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# Nginx (для фронтенда)
apt install -y nginx
```

---

## Шаг 4: Установите Ollama (если нужен GPU)

```bash
# Ollama с поддержкой GPU
curl -fsSL https://ollama.ai/install.sh | sh

# Запустите Ollama
systemctl enable ollama
systemctl start ollama

# Скачайте модели
ollama pull llama3.2
ollama pull qwen2.5
ollama pull qwen2.5vl:7b   # для vision
ollama pull moondream       # быстрый vision
```

---

## Шаг 5: Разверните бэкенд

```bash
# Клонируйте репозиторий
cd /opt
git clone https://github.com/your-org/ai-scraping-stack.git
cd ai-scraping-stack

# Создайте виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
scrapling install

# Создайте .env
cp .env.example .env
nano .env
# Заполните ключи (OPENROUTER_API_KEY и т.д.)

# Создайте директорию для данных
mkdir -p data/screenshots
```

---

## Шаг 6: Создайте systemd сервис

```bash
nano /etc/systemd/system/scrapling-api.service
```

```ini
[Unit]
Description=AI Scraping Stack API
After=network.target ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-scraping-stack
Environment="PATH=/opt/ai-scraping-stack/venv/bin"
ExecStart=/opt/ai-scraping-stack/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8100
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now scrapling-api
systemctl status scrapling-api
```

---

## Шаг 7: Настройте Nginx (фронтенд + прокси)

```bash
nano /etc/nginx/sites-available/scrapling
```

```nginx
server {
    listen 80;
    server_name ваш-домен.com;

    # Фронтенд (статический)
    root /opt/ai-scraping-stack;
    index landing.html;

    location / {
        try_files /landing.html =404;
    }

    # Бэкенд API (прокси)
    location /api/ {
        proxy_pass http://127.0.0.1:8100/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Для SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # Статические файлы
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
ln -s /etc/nginx/sites-available/scrapling /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Шаг 8: Обновите API_URL в landing.html

```javascript
// В landing.html замените:
const API_URL = '';  // Пусто — тот же домен, Nginx проксирует /api/ → :8100
```

Или укажите полный URL:
```javascript
const API_URL = 'https://ваш-домен.com/api';
```

---

## Шаг 9: Настройте HTTPS (Let's Encrypt)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ваш-домен.com
```

---

## Шаг 10: Настройте firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Проверка

```bash
# API
curl http://localhost:8100/
# → {"status":"ok","version":"1.0.0","docs":"/docs"}

# Ollama
curl http://localhost:11434/api/tags
# → {"models":[...]}

# Фронтенд
curl http://localhost/
# → HTML landing page
```

---

## Стоимость Timeweb

| Ресурс | Цена/мес |
|--------|----------|
| 4 vCPU, 8GB RAM, 40GB SSD | ~1 500₽ |
| GPU NVIDIA T4 | ~8 000₽ |
| Без GPU (только OpenRouter) | ~1 500₽ |
| Домен + SSL | ~500₽/год |

**Итого:** ~1 500₽/мес без GPU, ~10 000₽/мес с GPU.

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| Ollama не видит GPU | `ollama serve` с `CUDA_VISIBLE_DEVICES=0` |
| API не запускается | `journalctl -u scrapling-api -f` |
| Nginx 502 | Проверьте что API работает: `curl localhost:8100` |
| SSE не работает | Убедитесь `proxy_buffering off` в Nginx |
| Memory OOM | Уменьшите `max_concurrent` в .env |
