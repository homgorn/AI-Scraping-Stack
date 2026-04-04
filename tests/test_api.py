"""
tests/test_api.py — Integration tests for FastAPI endpoints
============================================================
Tests the full HTTP stack without external services.
Uses FastAPI TestClient (sync wrapper around async).
"""

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """TestClient with isolated settings."""
    from src.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


# ── Health & Status ───────────────────────────────────────────────────────────


class TestHealthEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_status(self, client):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert "ollama" in data
        assert "openrouter" in data
        assert "scrapling" in data

    def test_config(self, client):
        r = client.get("/config")
        assert r.status_code == 200
        data = r.json()
        assert "ollama_host" in data
        assert "default_ollama_model" in data

    def test_config_update(self, client):
        r = client.patch("/config", json={"max_concurrent": 10})
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ── Scrape Endpoints ──────────────────────────────────────────────────────────


class TestScrapeEndpoints:
    def test_scrape_invalid_url(self, client):
        """Scrape with empty URL should return 422."""
        r = client.post("/scrape", json={})
        assert r.status_code == 422

    def test_scrape_bulk_empty(self, client):
        """Bulk scrape with no URLs should return 422."""
        r = client.post("/scrape/bulk", json={"urls": []})
        assert r.status_code == 422

    def test_scrape_bulk_too_many(self, client):
        """Bulk scrape with >50 URLs should fail."""
        r = client.post(
            "/scrape/bulk",
            json={
                "urls": [f"https://example.com/{i}" for i in range(51)],
                "strategy": "free",
                "task": "summarize",
                "complexity": "low",
                "max_concurrent": 5,
            },
        )
        assert r.status_code == 422


# ── Model Management ──────────────────────────────────────────────────────────


class TestModelEndpoints:
    def test_list_models(self, client):
        r = client.get("/models")
        assert r.status_code == 200
        data = r.json()
        assert "ollama" in data
        assert "openrouter" in data
        assert "custom_apis" in data

    def test_search_openrouter_models(self, client):
        r = client.get("/models/openrouter/search?q=claude")
        assert r.status_code == 200
        data = r.json()
        assert "models" in data

    def test_search_free_only(self, client):
        r = client.get("/models/openrouter/search?free_only=true")
        assert r.status_code == 200
        data = r.json()
        for m in data["models"]:
            assert m["free"] is True

    def test_add_remove_openrouter_model(self, client):
        # Add
        r = client.post(
            "/models/openrouter",
            json={
                "model_id": "test/model:free",
                "name": "Test Model",
                "free": True,
                "tier": "low",
            },
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # Duplicate should fail
        r = client.post(
            "/models/openrouter",
            json={
                "model_id": "test/model:free",
                "name": "Test Model",
                "free": True,
                "tier": "low",
            },
        )
        assert r.status_code == 409

        # Remove
        r = client.delete("/models/openrouter/test%2Fmodel%3Afree")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_add_remove_custom_api(self, client):
        r = client.post(
            "/models/api",
            json={
                "name": "test-api",
                "base_url": "https://test.api/v1",
                "api_key": "test-key",
                "models": ["model1", "model2"],
            },
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

        r = client.delete("/models/api/test-api")
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ── History & Stats ───────────────────────────────────────────────────────────


class TestHistoryEndpoints:
    def test_history_empty(self, client):
        """Fresh DB should return empty history."""
        r = client.get("/history")
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data

    def test_stats_empty(self, client):
        """Fresh DB should return zero stats."""
        r = client.get("/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_scrapes"] == 0
        assert data["total_cost_usd"] == 0.0


# ── Vision Endpoints ──────────────────────────────────────────────────────────


class TestVisionEndpoints:
    def test_vision_models(self, client):
        r = client.get("/vision/models")
        assert r.status_code == 200
        data = r.json()
        assert "ollama_vision" in data or "tasks" in data

    def test_vision_analyze_no_image(self, client):
        """Should return 422 without screenshot."""
        r = client.post("/vision/analyze", json={})
        assert r.status_code == 422

    def test_sitemap_no_url(self, client):
        """Should return 422 without URL."""
        r = client.get("/sitemap")
        assert r.status_code == 422


# ── Screenshot Endpoints ──────────────────────────────────────────────────────


class TestScreenshotEndpoints:
    def test_screenshot_no_url(self, client):
        """Should return 422 without URL."""
        r = client.post("/screenshot", json={})
        assert r.status_code == 422

    def test_bulk_screenshot_too_many(self, client):
        """Should reject >50 URLs."""
        r = client.post(
            "/screenshot/bulk",
            json={
                "urls": [f"https://example.com/{i}" for i in range(51)],
            },
        )
        assert r.status_code == 400
