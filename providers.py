"""
providers.py — Unified adapter layer for all scraping providers
==============================================================
Добавь любой провайдер как drop-in замену или fallback.
Все адаптеры возвращают единый ScrapeResult.

Usage:
    from providers import ProviderRouter
    router = ProviderRouter(config)
    result = await router.scrape("https://example.com", strategy="smart")

Провайдеры (от бесплатных к платным):
  FREE / Open-source (self-hosted):
    - Scrapling      — основной, anti-bot, adaptive selectors
    - Crawl4AI       — LLM-ready markdown, local LLM, Apache 2.0
    - Jina Reader    — r.jina.ai prefix, 10M free tokens on signup

  CHEAP API (pay-per-use):
    - ScraperAPI     — $0.00049/req, 40M IPs, CAPTCHA solve
    - Scrapingdog    — $0.0002/req, fastest response time (5s avg)
    - ScrapingBee    — $0.0002/req, AI markdown output
    - ZenRows        — $0.000276/req
    - Scrape.do      — $29/mo flat, simple proxy+CAPTCHA

  SPECIALIZED / Higher cost:
    - Firecrawl      — $16/mo, best LLM-ready markdown, RAG-first
    - Zyte API       — 93% success rate, ML-based extraction
    - Bright Data    — enterprise, 150M IPs
    - Apify          — 10k+ prebuilt scrapers, $49/mo

Strategy "smart":
    1. Jina Reader  (free, instant, no setup)
    2. Scrapling    (local, adaptive)
    3. Crawl4AI     (local, LLM-ready)
    4. ScraperAPI   (fallback, paid)
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

import httpx

logger = logging.getLogger(__name__)

RETRY_MAX = int(os.getenv("RETRY_MAX", "2"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RESET_TIMEOUT = 30.0


# ── Unified result type ───────────────────────────────────────────────────────
@dataclass
class ScrapeResult:
    url: str
    markdown: str = ""
    text: str = ""
    html: str = ""
    title: str = ""
    links: list[str] = field(default_factory=list)
    provider: str = "unknown"
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None


# ── Jina Reader (FREE — no key needed, 10M tokens on signup) ─────────────────
class JinaAdapter:
    """
    r.jina.ai — просто prepend к URL.
    Возвращает clean markdown, готовый для LLM.
    FREE: без ключа, rate limit ~20 RPM.
    С ключом: 10M токенов бесплатно при регистрации.
    Docs: https://jina.ai/reader/
    """

    BASE = "https://r.jina.ai/"
    SEARCH = "https://s.jina.ai/"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")

    async def scrape(self, url: str, css_selector: str = "") -> ScrapeResult:
        headers = {"Accept": "application/json", "X-Return-Format": "markdown"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if css_selector:
            headers["X-Target-Selector"] = css_selector
        # ReaderLM-v2 для сложных страниц (3x токены, но качество выше)
        # headers["x-engine"] = "readerlm-v2"

        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(self.BASE + url, headers=headers)
                r.raise_for_status()
                data = r.json()
                return ScrapeResult(
                    url=url,
                    markdown=data.get("data", {}).get("content", ""),
                    title=data.get("data", {}).get("title", ""),
                    provider="jina_reader",
                    tokens_used=data.get("meta", {}).get("usage", {}).get("tokens", 0),
                    cost_usd=0.0,
                )
        except Exception as e:
            return ScrapeResult(url=url, provider="jina_reader", error=str(e))

    async def search(self, query: str) -> list[dict]:
        """Web search → top 5 results as markdown (для RAG/agents)"""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(self.SEARCH + query, headers=headers)
            r.raise_for_status()
            return r.json().get("data", [])


# ── Crawl4AI (FREE / open-source, LLM-native) ────────────────────────────────
class Crawl4AIAdapter:
    """
    Crawl4AI — лучший open-source LLM-ready краулер.
    58K+ GitHub stars, Apache 2.0, работает offline с Ollama.
    pip install crawl4ai
    Docs: https://github.com/unclecode/crawl4ai
    """

    async def scrape(self, url: str, css_selector: str = "") -> ScrapeResult:
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
            from crawl4ai.async_configs import BrowserConfig

            run_cfg = CrawlerRunConfig(
                word_count_threshold=10,
                excluded_tags=["form", "header", "footer", "nav"],
                exclude_external_links=True,
                remove_overlay_elements=True,
                cache_mode=CacheMode.BYPASS,
                css_selector=css_selector or None,
            )
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as c:
                result = await c.arun(url=url, config=run_cfg)
                if result.success:
                    return ScrapeResult(
                        url=url,
                        markdown=result.markdown or "",
                        html=result.html or "",
                        links=[
                            l["href"] for l in (result.links.get("internal", []))[:50]
                        ],
                        provider="crawl4ai",
                        cost_usd=0.0,
                    )
                return ScrapeResult(
                    url=url, provider="crawl4ai", error=result.error_message
                )
        except ImportError:
            return ScrapeResult(
                url=url,
                provider="crawl4ai",
                error="crawl4ai not installed: pip install crawl4ai",
            )
        except Exception as e:
            return ScrapeResult(url=url, provider="crawl4ai", error=str(e))


# ── ScraperAPI (pay-per-use, $0.00049/req at scale) ──────────────────────────
class ScraperAPIAdapter:
    """
    ScraperAPI — 40M IPs, CAPTCHA, JS rendering.
    Free: 1000 requests/month.
    Paid: от $49/mo, $0.00049/req at scale.
    Docs: https://scraperapi.com/documentation/
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("SCRAPERAPI_KEY", "")

    async def scrape(
        self, url: str, js_render: bool = False, premium: bool = False
    ) -> ScrapeResult:
        if not self.api_key:
            return ScrapeResult(
                url=url, provider="scraperapi", error="SCRAPERAPI_KEY not set"
            )
        params: dict = {"api_key": self.api_key, "url": url}
        if js_render:
            params["render"] = "true"
        if premium:
            params["premium"] = "true"  # residential IPs

        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.get("https://api.scraperapi.com", params=params)
                r.raise_for_status()
                html = r.text
                import re

                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
                return ScrapeResult(
                    url=url,
                    html=html,
                    text=text,
                    provider="scraperapi",
                    cost_usd=0.00049,
                )
        except Exception as e:
            return ScrapeResult(url=url, provider="scraperapi", error=str(e))


# ── Scrapingdog (fastest avg response ~5s, $0.0002/req) ──────────────────────
class ScrapingdogAdapter:
    """
    Scrapingdog — fastest in benchmarks (5.48s avg for Amazon).
    1000 free credits on signup.
    Docs: https://docs.scrapingdog.com/
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("SCRAPINGDOG_KEY", "")

    async def scrape(self, url: str, js_render: bool = False) -> ScrapeResult:
        if not self.api_key:
            return ScrapeResult(
                url=url, provider="scrapingdog", error="SCRAPINGDOG_KEY not set"
            )
        params: dict = {
            "api_key": self.api_key,
            "url": url,
            "dynamic": str(js_render).lower(),
        }
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.get("https://api.scrapingdog.com/scrape", params=params)
                r.raise_for_status()
                html = r.text
                import re

                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
                return ScrapeResult(
                    url=url,
                    html=html,
                    text=text,
                    provider="scrapingdog",
                    cost_usd=0.0002,
                )
        except Exception as e:
            return ScrapeResult(url=url, provider="scrapingdog", error=str(e))


# ── Firecrawl (best LLM-ready output, $16/mo starter) ───────────────────────
class FirecrawlAdapter:
    """
    Firecrawl — лидер для RAG/LLM пайплайнов.
    70k GitHub stars, AGPL-3.0.
    Hosted: $16/mo; Self-hosted: free.
    pip install firecrawl-py
    Docs: https://docs.firecrawl.dev/
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")

    async def scrape(self, url: str, formats: list[str] = None) -> ScrapeResult:
        if not self.api_key:
            return ScrapeResult(
                url=url, provider="firecrawl", error="FIRECRAWL_API_KEY not set"
            )
        try:
            from firecrawl import AsyncFirecrawlApp

            app = AsyncFirecrawlApp(api_key=self.api_key)
            data = await app.scrape_url(
                url,
                params={"formats": formats or ["markdown", "links"]},
            )
            return ScrapeResult(
                url=url,
                markdown=data.get("markdown", ""),
                links=data.get("links", [])[:50],
                title=data.get("metadata", {}).get("title", ""),
                provider="firecrawl",
                cost_usd=0.002,  # ~$2/1k pages on starter
            )
        except ImportError:
            # Fallback to raw HTTP
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"url": url, "formats": formats or ["markdown"]},
                )
                r.raise_for_status()
                data = r.json().get("data", {})
                return ScrapeResult(
                    url=url,
                    markdown=data.get("markdown", ""),
                    title=data.get("metadata", {}).get("title", ""),
                    provider="firecrawl",
                    cost_usd=0.002,
                )
        except Exception as e:
            return ScrapeResult(url=url, provider="firecrawl", error=str(e))

    async def crawl(self, url: str, max_pages: int = 10) -> list[ScrapeResult]:
        """Полный crawl сайта → список markdown страниц (для RAG)"""
        if not self.api_key:
            return [
                ScrapeResult(
                    url=url, provider="firecrawl", error="FIRECRAWL_API_KEY not set"
                )
            ]
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(
                "https://api.firecrawl.dev/v1/crawl",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "limit": max_pages,
                    "scrapeOptions": {"formats": ["markdown"]},
                },
            )
            r.raise_for_status()
            job_id = r.json()["id"]

            # Poll for results
            for _ in range(30):
                await asyncio.sleep(3)
                status = await c.get(
                    f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                data = status.json()
                if data["status"] == "completed":
                    return [
                        ScrapeResult(
                            url=p["metadata"]["sourceURL"],
                            markdown=p.get("markdown", ""),
                            provider="firecrawl",
                        )
                        for p in data.get("data", [])
                    ]
        return []


# ── ScrapeGraphAI (LLM-powered structured extraction) ────────────────────────
class ScrapeGraphAIAdapter:
    """
    ScrapeGraphAI — prompt → structured JSON, self-healing selectors.
    pip install scrapegraphai
    Работает с Ollama (бесплатно) или cloud LLMs.
    Docs: https://scrapegraphai.com/
    """

    def __init__(self, llm_config: dict = None, ollama_model: str = "llama3.2"):
        self.ollama_model = ollama_model
        self.llm_config = llm_config or {
            "model": f"ollama/{ollama_model}",
            "temperature": 0,
            "format": "json",
            "base_url": "http://localhost:11434",
        }

    async def scrape(self, url: str, prompt: str, schema: dict = None) -> ScrapeResult:
        try:
            from scrapegraphai.graphs import SmartScraperGraph

            graph = SmartScraperGraph(
                prompt=prompt,
                source=url,
                config={"llm": self.llm_config},
            )
            result = graph.run()
            import json as _json

            return ScrapeResult(
                url=url,
                text=_json.dumps(result, ensure_ascii=False),
                provider="scrapegraphai",
                cost_usd=0.0,
            )
        except ImportError:
            return ScrapeResult(
                url=url,
                provider="scrapegraphai",
                error="scrapegraphai not installed: pip install scrapegraphai",
            )
        except Exception as e:
            return ScrapeResult(url=url, provider="scrapegraphai", error=str(e))


# ── ZenRows (good price/performance balance) ─────────────────────────────────
class ZenRowsAdapter:
    """
    ZenRows — $0.000276/req, anti-bot, JS rendering.
    100 free credits on signup.
    Docs: https://docs.zenrows.com/
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("ZENROWS_KEY", "")

    async def scrape(
        self, url: str, js_render: bool = False, antibot: bool = True
    ) -> ScrapeResult:
        if not self.api_key:
            return ScrapeResult(
                url=url, provider="zenrows", error="ZENROWS_KEY not set"
            )
        params: dict = {
            "apikey": self.api_key,
            "url": url,
            "js_render": str(js_render).lower(),
            "antibot": str(antibot).lower(),
            "markdown_response": "true",
        }
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.get("https://api.zenrows.com/v1/", params=params)
                r.raise_for_status()
                return ScrapeResult(
                    url=url,
                    markdown=r.text,
                    provider="zenrows",
                    cost_usd=0.000276,
                )
        except Exception as e:
            return ScrapeResult(url=url, provider="zenrows", error=str(e))


# ── Smart Router ──────────────────────────────────────────────────────────────
class CircuitBreaker:
    """Simple circuit breaker for provider fallback."""

    def __init__(self, failure_threshold: int = CIRCUIT_FAILURE_THRESHOLD,
                 reset_timeout: float = CIRCUIT_RESET_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures: dict[str, int] = {}
        self.last_failure_time: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def record_failure(self, provider: str):
        async with self._lock:
            self.failures[provider] = self.failures.get(provider, 0) + 1
            self.last_failure_time[provider] = asyncio.get_event_loop().time()

    async def is_open(self, provider: str) -> bool:
        async with self._lock:
            if provider not in self.failures:
                return False
            if self.failures[provider] >= self.failure_threshold:
                last_fail = self.last_failure_time.get(provider, 0)
                now = asyncio.get_event_loop().time()
                if now - last_fail > self.reset_timeout:
                    self.failures[provider] = 0
                    return False
                return True
            return False

    async def record_success(self, provider: str):
        async with self._lock:
            self.failures[provider] = 0


class ProviderRouter:
    """
    Умный роутер — выбирает провайдера по цене/скорости/сложности.

    Стратегии:
      "free"    → Jina → Crawl4AI → Scrapling (0 стоимость, self-hosted)
      "fast"    → Scrapling fast mode (локально, без внешних запросов)
      "smart"   → Jina → Scrapling → Crawl4AI → ScraperAPI (каскад)
      "llm"     → Crawl4AI + Ollama (LLM-ready markdown, privacy)
      "ai"      → ScrapeGraphAI (prompt → JSON, semantic extraction)
      "premium" → Firecrawl (лучшее LLM-ready качество)
      "stealth" → Scrapling StealthyFetcher (Cloudflare bypass)
    """

    COST_PER_1K = {
        "jina_reader": 0.00,  # free tier
        "crawl4ai": 0.00,  # self-hosted
        "scrapling": 0.00,  # self-hosted
        "scrapingdog": 0.20,  # $0.0002/req
        "scraperapi": 0.49,  # $0.00049/req
        "zenrows": 0.28,  # $0.000276/req
        "scrapingbee": 0.20,  # ~$0.0002/req
        "firecrawl": 2.00,  # ~$0.002/page
    }

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.jina = JinaAdapter(cfg.get("jina_api_key", ""))
        self.crawl4ai = Crawl4AIAdapter()
        self.scraperapi = ScraperAPIAdapter(cfg.get("scraperapi_key", ""))
        self.scrapingdog = ScrapingdogAdapter(cfg.get("scrapingdog_key", ""))
        self.firecrawl = FirecrawlAdapter(cfg.get("firecrawl_api_key", ""))
        self.scrapegraph = ScrapeGraphAIAdapter(
            ollama_model=cfg.get("ollama_model", "llama3.2")
        )
        self.zenrows = ZenRowsAdapter(cfg.get("zenrows_key", ""))
        self._circuit = CircuitBreaker()
        self._provider_names = {
            "jina_reader": "jina",
            "crawl4ai": "crawl4ai",
            "scrapling_fast": "scrapling",
            "scrapling_stealth": "scrapling",
            "scraperapi": "scraperapi",
            "scrapingdog": "scrapingdog",
            "firecrawl": "firecrawl",
            "scrapegraphai": "scrapegraph",
            "zenrows": "zenrows",
        }

    async def _retry_with_backoff(
        self,
        fetch_fn: Callable,
        provider_name: str,
    ) -> ScrapeResult:
        """Execute with retry and circuit breaker."""
        last_error = None

        for attempt in range(RETRY_MAX + 1):
            if await self._circuit.is_open(provider_name):
                logger.debug(f"Circuit open for {provider_name}, skipping")
                return ScrapeResult(url="", provider=provider_name,
                                   error=f"Circuit breaker open for {provider_name}")

            try:
                result = await fetch_fn()
                if not result.error and (result.markdown or result.text or result.html):
                    await self._circuit.record_success(provider_name)
                    return result
                last_error = result.error
                if result.provider != "unknown" and attempt == RETRY_MAX:
                    await self._circuit.record_failure(provider_name)
                    logger.warning(f"Provider {result.provider} failed after all retries: {result.error}")
            except Exception as e:
                last_error = str(e)
                if attempt == RETRY_MAX:
                    await self._circuit.record_failure(provider_name)
                    logger.warning(f"Provider {provider_name} exception after all retries: {e}")

            if attempt < RETRY_MAX:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        return ScrapeResult(url="", provider=provider_name, error=last_error or "Max retries exceeded")

    async def scrape(
        self,
        url: str,
        strategy: Literal[
            "free", "fast", "smart", "llm", "ai", "premium", "stealth"
        ] = "smart",
        prompt: str = "",
        css_selector: str = "",
        fallback: bool = True,
    ) -> ScrapeResult:
        """
        Scrape с выбранной стратегией и автоматическим fallback.
        """
        chain = self._build_chain(strategy, prompt, url, css_selector)

        for fetch_fn in chain:
            provider_key = self._extract_provider_key(fetch_fn)
            result = await self._retry_with_backoff(fetch_fn, provider_key)

            if not result.error and (result.markdown or result.text or result.html):
                return result

            if not fallback:
                return result

        return ScrapeResult(url=url, error="All providers failed", provider="router")

    def _extract_provider_key(self, fetch_fn: Callable) -> str:
        """Extract provider key from lambda for circuit breaker."""
        if hasattr(fetch_fn, "__name__"):
            name = fetch_fn.__name__
            if name.startswith("_scrapling"):
                return "scrapling"
            return name
        return "unknown"

    def _build_chain(self, strategy, prompt, url, css_selector):
        """Returns list of async callables in priority order.
        Uses default arg pattern to avoid closure capture bugs."""
        match strategy:
            case "free":
                return [
                    lambda u=url, c=css_selector: self.jina.scrape(u, c),
                    lambda u=url, c=css_selector: self.crawl4ai.scrape(u, c),
                ]
            case "fast":
                return [lambda u=url, c=css_selector: self._scrapling_fast(u, c)]
            case "smart":
                return [
                    lambda u=url, c=css_selector: self.jina.scrape(u, c),
                    lambda u=url, c=css_selector: self._scrapling_fast(u, c),
                    lambda u=url, c=css_selector: self.crawl4ai.scrape(u, c),
                    lambda u=url: self.scraperapi.scrape(u),
                ]
            case "llm":
                return [lambda u=url, c=css_selector: self.crawl4ai.scrape(u, c)]
            case "ai":
                p = prompt or "Extract all main content and data as structured JSON"
                return [lambda u=url, pr=p: self.scrapegraph.scrape(u, pr)]
            case "premium":
                return [
                    lambda u=url: self.firecrawl.scrape(u),
                    lambda u=url, c=css_selector: self.crawl4ai.scrape(u, c),
                ]
            case "stealth":
                return [
                    lambda u=url, c=css_selector: self._scrapling_stealth(u, c),
                    lambda u=url: self.scrapingdog.scrape(u, js_render=True),
                    lambda u=url: self.scraperapi.scrape(
                        u, js_render=True, premium=True
                    ),
                ]
            case _:
                return [lambda u=url: self.jina.scrape(u)]

    async def _scrapling_fast(self, url: str, css_selector: str = "") -> ScrapeResult:
        try:
            from scrapling.fetchers import Fetcher

            page = await asyncio.to_thread(Fetcher().get, url)
            text = await asyncio.to_thread(page.get_all_text, ignore_tags=["script", "style"])
            els = []
            if css_selector:
                elements = await asyncio.to_thread(page.css, css_selector, auto_save=True)
                els = [e.text for e in elements if e.text][:50]
            title_el = await asyncio.to_thread(page.css, "title", first=True)
            title = title_el.text if title_el else ""
            return ScrapeResult(
                url=url,
                html=page.html,
                text=text,
                title=title,
                links=[],
                provider="scrapling_fast",
                cost_usd=0.0,
            )
        except Exception as e:
            return ScrapeResult(url=url, provider="scrapling_fast", error=str(e))

    async def _scrapling_stealth(
        self, url: str, css_selector: str = ""
    ) -> ScrapeResult:
        try:
            from scrapling.fetchers import StealthyFetcher

            page = await asyncio.to_thread(StealthyFetcher.fetch, url, headless=True, network_idle=True)
            text = await asyncio.to_thread(page.get_all_text, ignore_tags=["script", "style"])
            return ScrapeResult(
                url=url,
                html=page.html,
                text=text,
                provider="scrapling_stealth",
                cost_usd=0.0,
            )
        except Exception as e:
            return ScrapeResult(url=url, provider="scrapling_stealth", error=str(e))

    def estimate_cost(self, num_pages: int, strategy: str) -> dict:
        """Оценка стоимости для N страниц"""
        provider_costs = {
            "free": {"provider": "jina+crawl4ai", "cost": 0.0},
            "fast": {"provider": "scrapling", "cost": 0.0},
            "smart": {"provider": "jina→scrapling", "cost": 0.0},
            "llm": {"provider": "crawl4ai+ollama", "cost": 0.0},
            "ai": {"provider": "scrapegraph+ollama", "cost": 0.0},
            "premium": {"provider": "firecrawl", "cost": num_pages * 0.002},
            "stealth": {"provider": "scrapling_stealth", "cost": 0.0},
        }
        est = provider_costs.get(strategy, {"provider": "unknown", "cost": 0.0})
        return {
            "strategy": strategy,
            "pages": num_pages,
            "provider": est["provider"],
            "estimated_cost_usd": est["cost"],
            "cost_per_page": est["cost"] / num_pages if num_pages > 0 else 0,
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio, json

    async def test():
        router = ProviderRouter()

        print("=== Strategy: free (Jina Reader) ===")
        r = await router.scrape("https://example.com", strategy="free")
        print(f"Provider: {r.provider}, Error: {r.error}")
        print(f"Markdown preview: {r.markdown[:200]}\n")

        print("=== Cost estimates (1000 pages) ===")
        for s in ["free", "fast", "smart", "premium", "stealth"]:
            est = router.estimate_cost(1000, s)
            print(f"  {s:10} → {est['provider']:25} ${est['estimated_cost_usd']:.2f}")

    asyncio.run(test())
