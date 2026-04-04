# Начало работы

> Запустите AI Scraping Stack за 5 минут. Опыт не требуется.

## Требования

- **Python 3.11+** — [Скачать Python](https://www.python.org/downloads/)
- **Git** — [Установить Git](https://git-scm.com/downloads)
- **Ollama** (опционально, для локального ИИ) — [Установить Ollama](https://ollama.ai)

## Шаг 1: Клонируйте репозиторий

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
```

## Шаг 2: Установите зависимости

```bash
# Создайте виртуальное окружение (рекомендуется)
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Установите все зависимости
pip install -r requirements.txt

# Установите браузеры Scrapling
scrapling install
```

## Шаг 3: Настройте окружение

```bash
# Скопируйте пример конфига
cp .env.example .env

# Откройте .env в редакторе
# Минимум (всё работает без ключей):
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Опционально: Добавьте API-ключи для лучших результатов

```env
# OpenRouter — 300+ облачных моделей (есть бесплатный тир)
# Получить ключ: openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-...

# Jina Reader — выше лимит с ключом
# Получить ключ: jina.ai
JINA_API_KEY=jina_...
```

## Шаг 4: Установите локальные ИИ-модели (опционально)

```bash
# Базовая модель для анализа текста
ollama pull llama3.2

# Vision модели для анализа скриншотов
ollama pull qwen2.5vl:7b   # Лучшее качество
ollama pull moondream       # Быстрая, работает на CPU
```

## Шаг 5: Проверьте здоровье системы

```bash
python debug.py --full
```

Ожидаемый вывод:
```
✓ Config loads: .env parsed successfully
✓ ollama_host: http://localhost:11434
✓ Ollama server: online
✓ Scrapling: installed
```

## Шаг 6: Запустите сервер

```bash
uvicorn api:app --reload --port 8100
```

Сервер запущен на **http://localhost:8100**

## Шаг 7: Откройте дашборд

Откройте `landing.html` в браузере, или перейдите:
- **http://localhost:8100/docs** — Интерактивная документация API (Swagger)
- **landing.html** — Полный интерфейс

## Проверьте, что всё работает

```bash
# Тест health endpoint
curl http://localhost:8100/
# → {"status":"ok","version":"1.0.0"}

# Тест простого скрейпа
curl -X POST http://localhost:8100/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","strategy":"free","task":"summarize"}'
```

## Следующие шаги

- Прочитайте [Архитектуру](Architecture-RU) для понимания системы
- Изучите [API Справочник](API-Reference-RU) для всех эндпоинтов
- Проверьте [Деплой](Deployment-RU) для публикации онлайн
- Смотрите [Участие](Contributing-RU) для помощи проекту

## Решение проблем

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError: scrapling` | Запустите `pip install -r requirements.txt` |
| Ollama не отвечает | Запустите `ollama serve` |
| Порт 8100 занят | Используйте `--port 8101` или завершите другой процесс |
| Директория `data/` отсутствует | Запустите `mkdir -p data` |
