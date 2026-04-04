# Contributing

> How to contribute to AI Scraping Stack. All contributions are welcome!

## Development Setup

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov ruff
```

## Code Standards

### Architecture Rules

1. **`api.py` is THIN** — only HTTP routing. No business logic. Always delegates to `src/`.
2. **`src/config.py` only** — never `os.getenv()` outside this file.
3. **`src/models.py` only** — never define Pydantic models in `api.py`.
4. **`providers.py` is standalone** — no `src/` imports, usable without FastAPI.
5. **No circular imports** — order: `config → models → llm/scraper/storage → synthesizer → api`
6. **Files < 500 lines** — split into modules if larger.

### Style

- Use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Line length: 120 characters
- Type hints on all function signatures
- Docstrings on all public functions

```bash
# Lint
ruff check src/ api.py providers.py

# Format
ruff format src/ api.py providers.py
```

## Testing

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov=api --cov-report=term-missing

# Specific module
pytest tests/test_api.py -v
```

### Writing Tests

- Place tests in `tests/` directory
- Use `conftest.py` for shared fixtures
- Mock external API calls (never hit real APIs in tests)
- Test both success and error paths

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main` (`git checkout -b feature/my-feature`)
3. **Make changes** following code standards
4. **Write tests** for new functionality
5. **Run tests** — all must pass (`pytest tests/ -v`)
6. **Run linter** — no errors (`ruff check src/ api.py providers.py`)
7. **Commit** with descriptive message
8. **Push** and open a Pull Request

### PR Requirements

- [ ] All tests pass
- [ ] Linter passes (Ruff)
- [ ] No new circular imports
- [ ] Documentation updated (USAGE.md, CONTEXT_MAP.md if needed)
- [ ] PR description explains the change

## How to Contribute

### Add a Scraping Provider

1. Add class in `providers.py` (copy `JinaAdapter` pattern)
2. Add instance to `ProviderRouter.__init__`
3. Add to `_build_chain` for relevant strategies
4. Add env var in `src/config.py`
5. Add to `.env.example`
6. Write tests in `tests/test_providers.py`

### Add a New Endpoint

1. Schema in `src/models.py`
2. Logic in `src/llm.py` or `src/scraper.py` or new `src/X.py`
3. Thin route in `api.py`: validate → call service → return
4. Write integration test in `tests/test_api.py`
5. Document in `USAGE.md`

### Add a New LLM Task

1. Add to `TASK_PROMPTS` dict in `src/llm.py`
2. Add to task `<select>` in `landing.html`
3. Document in `skills/skill_llm.md`

### Add a New Vision Task

1. Add to `VISION_TASKS` dict in `src/vision.py`
2. Document in `skills/skill_screenshot.md`

## Branch Naming

- `feature/add-provider` — new feature
- `fix/closure-bug` — bug fix
- `docs/update-readme` — documentation
- `refactor/extract-llm` — code refactoring

## Commit Messages

Use conventional commits:

```
feat: add Firecrawl provider
fix: closure bug in _build_chain lambdas
docs: update USAGE.md with new endpoints
refactor: extract LLMRouter into separate module
test: add integration tests for /synthesize
```

## Reporting Issues

When reporting a bug, include:
- Python version (`python --version`)
- OS and platform
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
