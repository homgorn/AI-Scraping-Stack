# Участие в проекте

> Как внести вклад в AI Scraping Stack. Все contributions приветствуются!

## Настройка разработки

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov ruff
```

## Стандарты кода

### Правила архитектуры

1. **`api.py` тонкий** — только HTTP маршруты. Без бизнес-логики. Всегда делегирует в `src/`.
2. **Только `src/config.py`** — никогда `os.getenv()` вне этого файла.
3. **Только `src/models.py`** — никогда не определяйте Pydantic модели в `api.py`.
4. **`providers.py` автономный** — без импортов из `src/`, работает без FastAPI.
5. **Без циклических импортов** — порядок: `config → models → llm/scraper/storage → synthesizer → api`
6. **Файлы < 500 строк** — разбивайте на модули если больше.

### Стиль

- Используйте [Ruff](https://github.com/astral-sh/ruff) для линтинга и форматирования
- Длина строки: 120 символов
- Типизация на всех функциях
- Docstrings на всех публичных функциях

```bash
# Линтинг
ruff check src/ api.py providers.py

# Форматирование
ruff format src/ api.py providers.py
```

## Тестирование

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=src --cov=api --cov-report=term-missing

# Конкретный модуль
pytest tests/test_api.py -v
```

### Написание тестов

- Размещайте тесты в директории `tests/`
- Используйте `conftest.py` для общих фикстур
- Мокайте внешние API (не вызывайте реальные API в тестах)
- Тестируйте как успех, так и ошибки

## Процесс Pull Request

1. **Форкните** репозиторий
2. **Создайте ветку** от `main` (`git checkout -b feature/my-feature`)
3. **Внесите изменения** следуя стандартам
4. **Напишите тесты** для нового функционала
5. **Запустите тесты** — все должны пройти (`pytest tests/ -v`)
6. **Запустите линтер** — без ошибок (`ruff check src/ api.py providers.py`)
7. **Закоммитьте** с описательным сообщением
8. **Запушьте** и откройте Pull Request

### Требования к PR

- [ ] Все тесты проходят
- [ ] Линтер проходит (Ruff)
- [ ] Нет новых циклических импортов
- [ ] Документация обновлена (USAGE.md, CONTEXT_MAP.md при необходимости)
- [ ] Описание PR объясняет изменение

## Как внести вклад

### Добавить провайдер скрапинга

1. Добавьте класс в `providers.py` (скопируйте паттерн `JinaAdapter`)
2. Добавьте экземпляр в `ProviderRouter.__init__`
3. Добавьте в `_build_chain` для нужных стратегий
4. Добавьте env var в `src/config.py`
5. Добавьте в `.env.example`
6. Напишите тесты в `tests/test_providers.py`

### Добавить новый эндпоинт

1. Схема в `src/models.py`
2. Логика в `src/llm.py` или `src/scraper.py` или новый `src/X.py`
3. Тонкий маршрут в `api.py`: валидация → вызов сервиса → возврат
4. Напишите интеграционный тест в `tests/test_api.py`
5. Документируйте в `USAGE.md`

### Добавить новую задачу LLM

1. Добавьте в `TASK_PROMPTS` в `src/llm.py`
2. Добавьте в `<select>` задач в `landing.html`
3. Документируйте в `skills/skill_llm.md`

### Добавить новую задачу Vision

1. Добавьте в `VISION_TASKS` в `src/vision.py`
2. Документируйте в `skills/skill_screenshot.md`

## Именование веток

- `feature/add-provider` — новая функция
- `fix/closure-bug` — исправление бага
- `docs/update-readme` — документация
- `refactor/extract-llm` — рефакторинг кода

## Сообщения коммитов

Используйте conventional commits:

```
feat: add Firecrawl provider
fix: closure bug in _build_chain lambdas
docs: update USAGE.md with new endpoints
refactor: extract LLMRouter into separate module
test: add integration tests for /synthesize
```

## Сообщение об ошибках

При сообщении о баге укажите:
- Версию Python (`python --version`)
- ОС и платформу
- Шаги воспроизведения
- Ожидаемое и фактическое поведение
- Логи или сообщения об ошибках

## Лицензия

Внося вклад, вы соглашаетесь, что ваши изменения будут лицензированы под MIT License.
