"""
tests/test_vision.py — Vision service & model registry tests
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.vision import (
    ModelRegistry,
    VisionService,
    VisionResult,
    OPENROUTER_FREE_VISION,
    OLLAMA_VISION_MODELS,
    HF_VISION_MODELS,
    VISION_TASKS,
)


# ── ModelRegistry ─────────────────────────────────────────────────────────────

class TestModelRegistry:
    @pytest.fixture
    def registry(self, tmp_path):
        return ModelRegistry(registry_path=str(tmp_path / "vision_models.json"))

    def test_builtin_or_models_present(self, registry):
        models = registry.all_openrouter()
        ids = [m["id"] for m in models]
        assert "qwen/qwen3-vl-235b-a22b-thinking:free" in ids
        assert "nvidia/nemotron-nano-2-vl-12b:free" in ids
        assert "openrouter/auto" in ids

    def test_builtin_ollama_models_present(self, registry):
        models = registry.all_ollama()
        ids = [m["id"] for m in models]
        assert "qwen3-vl:30b" in ids
        assert "moondream" in ids
        assert "llava:7b" in ids

    def test_builtin_hf_models_present(self, registry):
        models = registry.all_hf()
        assert len(models) >= 2
        hf_ids = [m.get("hf_id", "") for m in models]
        assert any("Qwen" in hid for hid in hf_ids)

    def test_add_custom_openrouter_model(self, registry):
        model = {
            "id": "custom/test-vision:free",
            "name": "Test Vision",
            "provider": "openrouter",
            "free": True,
        }
        result = registry.add(model)
        assert result is True
        ids = [m["id"] for m in registry.all_openrouter()]
        assert "custom/test-vision:free" in ids

    def test_add_duplicate_returns_false(self, registry):
        model = {"id": "duplicate/model", "name": "Dup", "provider": "openrouter"}
        registry.add(model)
        result = registry.add(model)
        assert result is False

    def test_add_custom_ollama_model(self, registry):
        model = {"id": "my-model:7b", "name": "My Model", "provider": "ollama"}
        registry.add(model)
        ids = [m["id"] for m in registry.all_ollama()]
        assert "my-model:7b" in ids

    def test_add_custom_hf_model(self, registry):
        model = {
            "id": "org/CustomVisionModel",
            "hf_id": "org/CustomVisionModel",
            "name": "Custom HF",
            "provider": "huggingface",
        }
        registry.add(model)
        ids = [m["id"] for m in registry.all_hf()]
        assert "org/CustomVisionModel" in ids

    def test_add_custom_endpoint(self, registry):
        model = {
            "id": "my-endpoint",
            "name": "My Endpoint",
            "provider": "custom_endpoint",
            "base_url": "http://localhost:8000/v1",
            "api_key": "none",
            "models": ["vision-v1"],
        }
        registry.add(model)
        endpoints = registry.all_custom_endpoints()
        assert any(e["id"] == "my-endpoint" for e in endpoints)

    def test_remove_custom_model(self, registry):
        model = {"id": "to-remove", "name": "Remove", "provider": "openrouter"}
        registry.add(model)
        result = registry.remove("to-remove")
        assert result is True
        ids = [m["id"] for m in registry.all_openrouter()]
        assert "to-remove" not in ids

    def test_remove_nonexistent_returns_false(self, registry):
        assert registry.remove("does-not-exist") is False

    def test_persists_to_json(self, registry, tmp_path):
        model = {"id": "persistent/model", "name": "Persist", "provider": "openrouter"}
        registry.add(model)
        # Load fresh registry from same file
        registry2 = ModelRegistry(registry_path=str(tmp_path / "vision_models.json"))
        ids = [m["id"] for m in registry2.all_openrouter()]
        assert "persistent/model" in ids

    def test_to_dict_structure(self, registry):
        d = registry.to_dict()
        assert "openrouter_free" in d
        assert "ollama" in d
        assert "huggingface" in d
        assert "custom_endpoints" in d
        assert "total" in d
        assert d["total"] >= len(OPENROUTER_FREE_VISION)

    def test_total_count_correct(self, registry):
        d = registry.to_dict()
        expected = (len(registry.all_openrouter()) + len(registry.all_ollama())
                    + len(registry.all_hf()) + len(registry.all_custom_endpoints()))
        assert d["total"] == expected

    def test_corrupt_json_handled_gracefully(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("{{not valid json{{")
        registry = ModelRegistry(registry_path=str(path))
        # Should not raise, just use empty custom list
        assert isinstance(registry.all_openrouter(), list)


# ── VisionService ─────────────────────────────────────────────────────────────

class TestVisionService:
    @pytest.fixture
    def registry(self, tmp_path):
        return ModelRegistry(registry_path=str(tmp_path / "vm.json"))

    @pytest.fixture
    def vision(self, settings, registry):
        return VisionService(settings, registry)

    @pytest.fixture
    def vision_no_keys(self, settings_no_keys, registry):
        return VisionService(settings_no_keys, registry)

    # ── Prompt building ─────────────────────────────────────────────────────

    def test_build_prompt_business_intel(self, vision):
        p = vision._build_prompt("business_intel")
        assert "JSON" in p
        assert "company" in p.lower()

    def test_build_prompt_design_audit(self, vision):
        p = vision._build_prompt("design_audit")
        assert "UX" in p or "design" in p.lower()

    def test_build_prompt_custom(self, vision):
        p = vision._build_prompt("custom", "Extract all phone numbers")
        assert "Extract all phone numbers" in p

    def test_build_prompt_unknown_task_uses_summary(self, vision):
        p = vision._build_prompt("unknown_task_xyz")
        assert "webpage" in p.lower() or "describe" in p.lower()

    def test_all_tasks_produce_nonempty_prompts(self, vision):
        for task in VISION_TASKS:
            if task == "custom":
                continue
            p = vision._build_prompt(task)
            assert len(p) > 20, f"Task {task} produced short prompt"

    # ── Provider cascade ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_auto_tries_ollama_first(self, vision, sample_screenshot_b64):
        ollama_result = VisionResult(analysis="ollama result", model_used="ollama/qwen3-vl")
        or_result = VisionResult(analysis="or result", model_used="openrouter/model")
        vision._try_ollama = AsyncMock(return_value=ollama_result)
        vision._try_openrouter = AsyncMock(return_value=or_result)

        result = await vision.analyze_screenshot(sample_screenshot_b64, task="summary")
        vision._try_ollama.assert_called_once()
        vision._try_openrouter.assert_not_called()
        assert result.analysis == "ollama result"

    @pytest.mark.asyncio
    async def test_auto_falls_back_to_or_when_ollama_fails(self, vision, sample_screenshot_b64):
        vision._try_ollama = AsyncMock(return_value=VisionResult(error="no model"))
        vision._try_openrouter = AsyncMock(
            return_value=VisionResult(analysis="cloud result", model_used="openrouter/qwen"))
        vision._try_huggingface = AsyncMock(return_value=VisionResult(error="no token"))

        result = await vision.analyze_screenshot(sample_screenshot_b64, task="summary")
        vision._try_openrouter.assert_called_once()
        assert result.analysis == "cloud result"

    @pytest.mark.asyncio
    async def test_force_provider_ollama(self, vision, sample_screenshot_b64):
        vision._try_ollama = AsyncMock(return_value=VisionResult(analysis="local"))
        vision._try_openrouter = AsyncMock(return_value=VisionResult(analysis="cloud"))

        result = await vision.analyze_screenshot(
            sample_screenshot_b64, force_provider="ollama")
        vision._try_ollama.assert_called_once()
        vision._try_openrouter.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_provider_openrouter(self, vision, sample_screenshot_b64):
        vision._try_openrouter = AsyncMock(return_value=VisionResult(analysis="cloud"))
        vision._try_ollama = AsyncMock(return_value=VisionResult(analysis="local"))

        result = await vision.analyze_screenshot(
            sample_screenshot_b64, force_provider="openrouter")
        vision._try_openrouter.assert_called_once()
        vision._try_ollama.assert_not_called()

    @pytest.mark.asyncio
    async def test_url_and_task_set_on_result(self, vision, sample_screenshot_b64):
        vision._try_ollama = AsyncMock(
            return_value=VisionResult(analysis="ok", model_used="ollama/m"))
        result = await vision.analyze_screenshot(
            sample_screenshot_b64, task="design_audit", url="https://test.com")
        assert result.url == "https://test.com"
        assert result.task == "design_audit"

    @pytest.mark.asyncio
    async def test_elapsed_ms_set(self, vision, sample_screenshot_b64):
        vision._try_ollama = AsyncMock(return_value=VisionResult(analysis="ok"))
        result = await vision.analyze_screenshot(sample_screenshot_b64)
        assert isinstance(result.elapsed_ms, int) and result.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_analyze_many(self, vision, sample_screenshot_b64):
        vision._try_ollama = AsyncMock(return_value=VisionResult(analysis="result"))
        items = [
            {"url": "https://a.com", "screenshot_b64": sample_screenshot_b64},
            {"url": "https://b.com", "screenshot_b64": sample_screenshot_b64},
        ]
        results = await vision.analyze_many(items, task="summary", max_concurrent=2)
        assert len(results) == 2
        assert all(r.analysis == "result" for r in results)

    # ── HF backend ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_hf_fails_without_token(self, vision_no_keys, sample_screenshot_b64):
        result = await vision_no_keys._try_huggingface(sample_screenshot_b64, "test")
        assert result.error is not None
        assert "HF_TOKEN" in result.error

    @pytest.mark.asyncio
    async def test_or_fails_without_key(self, vision_no_keys, sample_screenshot_b64):
        result = await vision_no_keys._try_openrouter(sample_screenshot_b64, "test")
        assert result.error is not None

    # ── list_models ─────────────────────────────────────────────────────────

    def test_list_models_structure(self, vision):
        d = vision.list_models()
        assert "openrouter_free" in d
        assert "ollama" in d
        assert isinstance(d["total"], int) and d["total"] > 0


# ── Vision constants ──────────────────────────────────────────────────────────

class TestVisionConstants:
    def test_openrouter_free_all_marked_free(self):
        for m in OPENROUTER_FREE_VISION:
            assert m.get("free") is True, f"{m['id']} not marked free"

    def test_openrouter_free_have_context(self):
        for m in OPENROUTER_FREE_VISION:
            assert "context" in m and m["context"] > 0

    def test_ollama_all_have_pull_command(self):
        for m in OLLAMA_VISION_MODELS:
            assert "pull" in m and "ollama pull" in m["pull"]

    def test_ollama_all_have_vram_info(self):
        for m in OLLAMA_VISION_MODELS:
            assert "vram_gb" in m and m["vram_gb"] > 0

    def test_hf_all_have_hf_id(self):
        for m in HF_VISION_MODELS:
            assert "hf_id" in m and "/" in m["hf_id"]

    def test_vision_tasks_nonempty_skips_custom(self):
        for task, prompt in VISION_TASKS.items():
            if task == "custom":
                continue
            assert len(prompt) > 20, f"Task {task} has short prompt"
