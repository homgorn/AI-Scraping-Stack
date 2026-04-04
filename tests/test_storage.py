"""
tests/test_storage.py — Storage layer tests (SQLite + JSON)
"""
import pytest
from pathlib import Path
from src.storage import Storage
from src.models import ScrapeResult


@pytest.fixture
def storage(settings):
    return Storage(settings)


@pytest.fixture
async def initialized_storage(storage):
    await storage.init()
    return storage


def make_result(**kwargs) -> ScrapeResult:
    defaults = dict(
        url="https://example.com",
        provider="scrapling",
        mode="fast",
        task="summarize",
        analysis="Test analysis",
        model_used="ollama/llama3.2",
        html_length=5000,
        text_length=2000,
        cost_usd=0.0,
        elapsed_ms=1200,
    )
    defaults.update(kwargs)
    return ScrapeResult(**defaults)


# ── Init ──────────────────────────────────────────────────────────────────────

class TestStorageInit:
    @pytest.mark.asyncio
    async def test_init_creates_db_file(self, storage):
        await storage.init()
        from pathlib import Path  # noqa
        assert Path(storage.db_path).exists()

    @pytest.mark.asyncio
    async def test_init_creates_models_json(self, storage):
        await storage.init()
        assert storage.models_path.exists()

    @pytest.mark.asyncio
    async def test_init_idempotent(self, storage):
        await storage.init()
        await storage.init()  # second call should not raise
        assert Path(storage.db_path).exists()

    @pytest.mark.asyncio
    async def test_models_json_valid_on_init(self, storage):
        await storage.init()
        import json
        data = json.loads(storage.models_path.read_text())
        assert "openrouter" in data
        assert "custom_apis" in data


# ── History CRUD ──────────────────────────────────────────────────────────────

class TestScrapeHistory:
    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, initialized_storage):
        result = make_result(url="https://test.com", analysis="hello")
        await initialized_storage.save_result(result)
        history = await initialized_storage.get_history(limit=10)
        assert len(history) == 1
        assert history[0]["url"] == "https://test.com"

    @pytest.mark.asyncio
    async def test_multiple_results_ordered_newest_first(self, initialized_storage):
        for i in range(3):
            r = make_result(url=f"https://site{i}.com", analysis=f"analysis {i}")
            await initialized_storage.save_result(r)
        history = await initialized_storage.get_history(limit=10)
        assert len(history) == 3
        # Most recent first (highest id)
        assert history[0]["url"] == "https://site2.com"

    @pytest.mark.asyncio
    async def test_limit_respected(self, initialized_storage):
        for i in range(10):
            await initialized_storage.save_result(make_result(url=f"https://s{i}.com"))
        history = await initialized_storage.get_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_url_filter(self, initialized_storage):
        await initialized_storage.save_result(make_result(url="https://example.com/page1"))
        await initialized_storage.save_result(make_result(url="https://other.com"))
        history = await initialized_storage.get_history(url_filter="example.com")
        assert len(history) == 1
        assert "example.com" in history[0]["url"]

    @pytest.mark.asyncio
    async def test_analysis_truncated_to_2000(self, initialized_storage):
        long_analysis = "x" * 5000
        await initialized_storage.save_result(make_result(analysis=long_analysis))
        history = await initialized_storage.get_history()
        assert len(history[0]["analysis"]) <= 2000

    @pytest.mark.asyncio
    async def test_error_result_saved(self, initialized_storage):
        result = make_result(error="Connection timeout", analysis="")
        await initialized_storage.save_result(result)
        history = await initialized_storage.get_history()
        assert history[0]["error"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_empty_history_returns_list(self, initialized_storage):
        history = await initialized_storage.get_history()
        assert history == []


# ── Stats ─────────────────────────────────────────────────────────────────────

class TestStats:
    @pytest.mark.asyncio
    async def test_stats_empty(self, initialized_storage):
        stats = await initialized_storage.get_stats()
        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["total_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_stats_with_results(self, initialized_storage):
        await initialized_storage.save_result(make_result(cost_usd=0.002, elapsed_ms=1000))
        await initialized_storage.save_result(make_result(cost_usd=0.003, elapsed_ms=2000))
        await initialized_storage.save_result(make_result(error="fail", cost_usd=0.0))
        stats = await initialized_storage.get_stats()
        assert stats["total"] == 3
        assert stats["success"] == 2  # ones without error
        assert abs(stats["total_cost_usd"] - 0.005) < 0.0001
        assert stats["avg_ms"] == 1400  # (1000+2000+1200)/3

    @pytest.mark.asyncio
    async def test_stats_has_last_scrape(self, initialized_storage):
        await initialized_storage.save_result(make_result())
        stats = await initialized_storage.get_stats()
        assert stats["last_scrape"] != ""


# ── Config overrides ──────────────────────────────────────────────────────────

class TestConfigOverrides:
    @pytest.mark.asyncio
    async def test_set_and_get_override(self, initialized_storage):
        await initialized_storage.set_config_override("ollama_model", "mistral")
        val = await initialized_storage.get_config_override("ollama_model")
        assert val == "mistral"

    @pytest.mark.asyncio
    async def test_nonexistent_key_returns_none(self, initialized_storage):
        val = await initialized_storage.get_config_override("nonexistent_key")
        assert val is None

    @pytest.mark.asyncio
    async def test_override_updates_existing(self, initialized_storage):
        await initialized_storage.set_config_override("key", "value1")
        await initialized_storage.set_config_override("key", "value2")
        val = await initialized_storage.get_config_override("key")
        assert val == "value2"


# ── Custom models JSON ────────────────────────────────────────────────────────

class TestCustomModelsJSON:
    @pytest.mark.asyncio
    async def test_add_and_retrieve_openrouter_model(self, initialized_storage):
        model = {"id": "test/model:free", "name": "Test", "provider": "openrouter"}
        await initialized_storage.add_openrouter_model(model)
        models = await initialized_storage.get_custom_openrouter_models()
        assert any(m["id"] == "test/model:free" for m in models)

    @pytest.mark.asyncio
    async def test_duplicate_openrouter_model_not_added(self, initialized_storage):
        model = {"id": "same/model", "name": "Same"}
        await initialized_storage.add_openrouter_model(model)
        await initialized_storage.add_openrouter_model(model)
        models = await initialized_storage.get_custom_openrouter_models()
        assert sum(1 for m in models if m["id"] == "same/model") == 1

    @pytest.mark.asyncio
    async def test_remove_openrouter_model(self, initialized_storage):
        model = {"id": "remove/me", "name": "Remove"}
        await initialized_storage.add_openrouter_model(model)
        await initialized_storage.remove_openrouter_model("remove/me")
        models = await initialized_storage.get_custom_openrouter_models()
        assert not any(m["id"] == "remove/me" for m in models)

    @pytest.mark.asyncio
    async def test_add_and_retrieve_custom_api(self, initialized_storage):
        api = {"name": "Groq", "base_url": "https://api.groq.com/v1",
               "api_key": "secret", "models": ["llama3"]}
        await initialized_storage.add_custom_api(api)
        apis = await initialized_storage.get_custom_apis()
        assert any(a["name"] == "Groq" for a in apis)

    @pytest.mark.asyncio
    async def test_remove_custom_api(self, initialized_storage):
        api = {"name": "ToRemove", "base_url": "http://x", "api_key": "k", "models": []}
        await initialized_storage.add_custom_api(api)
        await initialized_storage.remove_custom_api("ToRemove")
        apis = await initialized_storage.get_custom_apis()
        assert not any(a["name"] == "ToRemove" for a in apis)
