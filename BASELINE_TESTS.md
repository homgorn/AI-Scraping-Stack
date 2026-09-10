# Baseline test status (pre-hardening)

**Branch:** `harden/v0.4.1`
**Python:** 3.12.8
**Command:** `PYTHONPATH=. pytest -q --no-header`

```
27 failed, 92 passed, 1 warning in 72.34s
```

## Why tests don't run cleanly without `PYTHONPATH=.`

`tests/conftest.py:13` does `from src.config import Settings`, but `src/` is not
on `sys.path` when `pytest` is invoked without an editable install. Workaround:
`PYTHONPATH=. pytest ...`. We keep that for now; will fix via `[tool.pytest.ini_options]`
`pythonpath = ["."]` in a later PR (out of scope for v0.4.1 hardening).

## Failures are pre-existing and not caused by v0.4.1 changes

All 27 failures are caused by API drift between `src/models.py` (current) and
`tests/test_storage.py` / `tests/test_api.py` (older fixture shape).

Example root cause: tests construct `ScrapeResult(url=..., analysis=..., mode=...)`,
but `src/models.py` exports no `ScrapeResult` class at all. The current code
passes `ScrapeResponse` / `HistoryEntry` instead.

`tests/test_storage.py::TestStorageInit::test_init_creates_db_file` fails with
`AttributeError`, suggesting `Storage.__init__` signature also changed.

## Strategy for v0.4.1

- **Do not** try to fix these 27 failures in this PR (scope = security hardening).
- **Do not** regress any of the 92 passing tests.
- After hardening is merged, file a follow-up issue "Tests are out of sync with
  current API — restore coverage before v0.5" and fix in a dedicated PR.
