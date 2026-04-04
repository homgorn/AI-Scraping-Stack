"""
tests/conftest.py — Shared fixtures
"""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import Settings, get_settings


# ── Settings fixture ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear lru_cache before each test so settings don't bleed."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings(tmp_path):
    """Isolated Settings using temp dir for data files."""
    return Settings(
        ollama_host="http://localhost:11434",
        ollama_model="llama3.2",
        openrouter_api_key="test-or-key",
        openrouter_model="anthropic/claude-3.5-sonnet",
        db_path=str(tmp_path / "test_history.db"),
        model_registry_path=str(tmp_path / "test_models.json"),
    )


@pytest.fixture
def settings_no_keys(tmp_path):
    """Settings with no API keys — tests offline/local-only path."""
    return Settings(
        ollama_host="http://localhost:11434",
        ollama_model="llama3.2",
        openrouter_api_key="",
        db_path=str(tmp_path / "test_history.db"),
        model_registry_path=str(tmp_path / "test_models.json"),
    )


# ── HTTP mock helpers ─────────────────────────────────────────────────────────


def make_httpx_response(status: int = 200, json_data: dict = None, text: str = ""):
    """Create a mock httpx Response."""
    mock = MagicMock()
    mock.status_code = status
    mock.text = text or (json.dumps(json_data) if json_data else "")
    mock.json = MagicMock(return_value=json_data or {})
    mock.raise_for_status = MagicMock()
    if status >= 400:
        from httpx import HTTPStatusError

        mock.raise_for_status.side_effect = HTTPStatusError(f"HTTP {status}", request=MagicMock(), response=mock)
    return mock


def make_ollama_response(content: str, model: str = "llama3.2") -> dict:
    return {"message": {"role": "assistant", "content": content}}


def make_openrouter_response(content: str, model: str = "claude-3.5-sonnet") -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "model": model,
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }


def make_jina_response(markdown: str, title: str = "Test Page") -> dict:
    return {
        "data": {"content": markdown, "title": title},
        "meta": {"usage": {"tokens": len(markdown) // 4}},
    }


# ── Screenshot fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def sample_screenshot_b64():
    """Minimal valid PNG as base64 (1x1 white pixel)."""
    # Actual 1x1 PNG bytes
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc"
        b"\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return base64.b64encode(png_1x1).decode()


@pytest.fixture
def sample_html():
    return """<!DOCTYPE html>
<html>
<head><title>Acme SaaS — AI Platform</title></head>
<body>
<nav><a href="/">Home</a> <a href="/pricing">Pricing</a></nav>
<h1>AI-powered workflow automation</h1>
<p>Acme helps teams save 10 hours/week with intelligent automation.</p>
<div class="price">$49/mo</div>
<a href="/signup">Start free trial</a>
</body>
</html>"""


@pytest.fixture
def sample_robots_txt():
    return """User-agent: *
Disallow: /admin/
Disallow: /api/internal/
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap_blog.xml"""


@pytest.fixture
def sample_sitemap_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/pricing</loc></url>
  <url><loc>https://example.com/features</loc></url>
  <url><loc>https://example.com/blog</loc></url>
</urlset>"""


# ── Async helpers ─────────────────────────────────────────────────────────────


class AsyncContextManagerMock:
    """Mock async context manager (for httpx.AsyncClient)."""

    def __init__(self, return_value):
        self._return_value = return_value

    async def __aenter__(self):
        return self._return_value

    async def __aexit__(self, *args):
        pass
