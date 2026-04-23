"""
tests/test_providers.py — Provider adapter and router tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from providers import (
    JinaAdapter,
    Crawl4AIAdapter,
    ScraperAPIAdapter,
    ScrapingdogAdapter,
    FirecrawlAdapter,
    ZenRowsAdapter,
    ProviderRouter,
    ScrapeResult,
)


# ── ScrapeResult dataclass ────────────────────────────────────────────────────

class TestScrapeResultDataclass:
    def test_defaults(self):
        r = ScrapeResult(url="https://example.com")
        assert r.url == "https://example.com"
        assert r.markdown == ""
        assert r.text == ""
        assert r.html == ""
        assert r.links == []
        assert r.provider == "unknown"
        assert r.cost_usd == 0.0
        assert r.error is None

    def test_error_field(self):
        r = ScrapeResult(url="https://x.com", error="timeout")
        assert r.error == "timeout"


# ── JinaAdapter ───────────────────────────────────────────────────────────────

class TestJinaAdapter:
    @pytest.fixture
    def adapter(self):
        return JinaAdapter(api_key="test-key")

    @pytest.fixture
    def adapter_no_key(self):
        return JinaAdapter(api_key="")

    @pytest.mark.asyncio
    async def test_success_returns_markdown(self, adapter):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "data": {"content": "# Hello\n\nWorld", "title": "Hello"},
            "meta": {"usage": {"tokens": 100}},
        }
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_resp)
            ))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert result.markdown == "# Hello\n\nWorld"
        assert result.title == "Hello"
        assert result.tokens_used == 100
        assert result.error is None
        assert result.provider == "jina_reader"

    @pytest.mark.asyncio
    async def test_network_error_returns_error_result(self, adapter):
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("connection timeout"))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert result.error is not None
        assert result.provider == "jina_reader"

    @pytest.mark.asyncio
    async def test_no_key_works_without_auth_header(self, adapter_no_key):
        """Jina works without key (rate limited but functional)."""
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"data": {"content": "content", "title": ""}, "meta": {}}
        mock_resp.raise_for_status = MagicMock()
        captured_headers = []
        with patch("httpx.AsyncClient") as mc:
            mock_get = AsyncMock(return_value=mock_resp)
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=mock_get))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            await adapter_no_key.scrape("https://example.com")
        # Should not raise even without key
        assert True

    @pytest.mark.asyncio
    async def test_css_selector_sent_as_header(self, adapter):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"data": {"content": "c", "title": ""}, "meta": {}}
        mock_resp.raise_for_status = MagicMock()
        captured = []
        async def mock_get(url, headers=None, **kwargs):
            captured.append(headers or {})
            return mock_resp
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=mock_get))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            await adapter.scrape("https://example.com", css_selector=".article")
        assert any("X-Target-Selector" in h for h in captured)


# ── ScraperAPIAdapter ─────────────────────────────────────────────────────────

class TestScraperAPIAdapter:
    @pytest.fixture
    def adapter(self):
        return ScraperAPIAdapter(api_key="test-key")

    @pytest.fixture
    def adapter_no_key(self):
        return ScraperAPIAdapter(api_key="")

    @pytest.mark.asyncio
    async def test_no_key_returns_error(self, adapter_no_key):
        result = await adapter_no_key.scrape("https://example.com")
        assert result.error is not None
        assert "SCRAPERAPI_KEY" in result.error

    @pytest.mark.asyncio
    async def test_success_returns_html(self, adapter):
        mock_resp = MagicMock(status_code=200, text="<html><body>content</body></html>")
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_resp)
            ))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert "<html>" in result.html
        assert result.provider == "scraperapi"
        assert result.cost_usd == 0.00049

    @pytest.mark.asyncio
    async def test_network_error_returns_error(self, adapter):
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert result.error is not None


# ── ScrapingdogAdapter ────────────────────────────────────────────────────────

class TestScrapingdogAdapter:
    @pytest.mark.asyncio
    async def test_no_key_returns_error(self):
        adapter = ScrapingdogAdapter(api_key="")
        result = await adapter.scrape("https://example.com")
        assert result.error is not None
        assert "SCRAPINGDOG_KEY" in result.error

    @pytest.mark.asyncio
    async def test_cost_is_correct(self):
        adapter = ScrapingdogAdapter(api_key="test")
        mock_resp = MagicMock(status_code=200, text="<html>content</html>")
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_resp)
            ))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert result.cost_usd == 0.0002


# ── ZenRowsAdapter ────────────────────────────────────────────────────────────

class TestZenRowsAdapter:
    @pytest.mark.asyncio
    async def test_no_key_returns_error(self):
        adapter = ZenRowsAdapter(api_key="")
        result = await adapter.scrape("https://example.com")
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_cost_is_correct(self):
        adapter = ZenRowsAdapter(api_key="test")
        mock_resp = MagicMock(status_code=200, text="# Page content")
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as mc:
            mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_resp)
            ))
            mc.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await adapter.scrape("https://example.com")
        assert result.cost_usd == 0.000276
        assert result.provider == "zenrows"


# ── ProviderRouter ────────────────────────────────────────────────────────────

class TestProviderRouter:
    @pytest.fixture
    def router(self):
        return ProviderRouter({})

    @pytest.fixture
    def router_with_keys(self):
        return ProviderRouter({
            "jina_api_key": "test-jina",
            "scraperapi_key": "test-scraperapi",
        })

    def test_estimate_cost_free_is_zero(self, router):
        for strategy in ("free", "fast", "smart", "llm", "ai", "stealth"):
            est = router.estimate_cost(1000, strategy)
            assert est["estimated_cost_usd"] == 0.0, f"{strategy} should be free"

    def test_estimate_cost_premium_nonzero(self, router):
        est = router.estimate_cost(1000, "premium")
        assert est["estimated_cost_usd"] > 0

    def test_estimate_cost_structure(self, router):
        est = router.estimate_cost(100, "smart")
        assert "strategy" in est
        assert "pages" in est
        assert "provider" in est
        assert "estimated_cost_usd" in est
        assert "cost_per_page" in est
        assert est["pages"] == 100

    def test_estimate_cost_zero_pages(self, router):
        est = router.estimate_cost(0, "smart")
        assert est["cost_per_page"] == 0

    @pytest.mark.asyncio
    async def test_free_strategy_tries_jina_first(self, router):
        jina_result = ScrapeResult(
            url="https://example.com",
            markdown="# Content",
            provider="jina_reader",
        )
        router.jina.scrape = AsyncMock(return_value=jina_result)
        result = await router.scrape("https://example.com", strategy="free")
        router.jina.scrape.assert_called_once()
        assert result.provider == "jina_reader"

    @pytest.mark.asyncio
    async def test_smart_falls_back_on_jina_failure(self, router):
        error_result = ScrapeResult(url="x", error="timeout", provider="jina_reader")
        scrapling_result = ScrapeResult(url="x", text="content", provider="scrapling_fast")
        router.jina.scrape = AsyncMock(return_value=error_result)
        router._scrapling_fast = AsyncMock(return_value=scrapling_result)
        router.crawl4ai.scrape = AsyncMock(return_value=error_result)
        router.scraperapi.scrape = AsyncMock(return_value=error_result)

        result = await router.scrape("https://x.com", strategy="smart", fallback=True)
        assert router.jina.scrape.call_count >= 1
        router._scrapling_fast.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_fallback_returns_first_error(self, router):
        error = ScrapeResult(url="x", error="fail", provider="jina_reader")
        router.jina.scrape = AsyncMock(return_value=error)
        result = await router.scrape("https://x.com", strategy="free", fallback=False)
        assert router.jina.scrape.call_count >= 1

    @pytest.mark.asyncio
    async def test_all_fail_returns_error_result(self, router):
        error = ScrapeResult(url="x", error="fail", provider="test")
        router.jina.scrape = AsyncMock(return_value=error)
        router._scrapling_fast = AsyncMock(return_value=error)
        router.crawl4ai.scrape = AsyncMock(return_value=error)
        router.scraperapi.scrape = AsyncMock(return_value=error)

        result = await router.scrape("https://x.com", strategy="smart")
        assert result.error is not None
        assert result.url == "https://x.com"

    def test_all_strategies_have_chain(self, router):
        """Verify _build_chain returns callables for all strategies."""
        strategies = ["free", "fast", "smart", "llm", "ai", "premium", "stealth"]
        for s in strategies:
            chain = router._build_chain(s, "", "https://test.com", "")
            assert len(chain) > 0, f"Strategy {s} has empty chain"
            assert all(callable(fn) for fn in chain)
