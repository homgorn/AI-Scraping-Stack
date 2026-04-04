"""
src/scraper.py — ScraperService: fetch orchestration
=====================================================
Delegates to ProviderRouter for actual fetching.
Optionally runs LLM analysis on scraped content.

Usage:
    from src.scraper import ScraperService
    from src.config import get_settings
    svc = ScraperService(get_settings())
    result = await svc.scrape(ScrapeRequest(url="https://example.com"))
"""

import time
from typing import Optional

from src.config import Settings
from src.models import ScrapeRequest, ScrapeResponse
from src.llm import LLMRouter


class ScraperService:
    """Orchestrates scraping + optional LLM analysis."""

    def __init__(self, settings: Settings):
        self.cfg = settings
        self._llm: Optional[LLMRouter] = None

    @property
    def llm(self) -> LLMRouter:
        if self._llm is None:
            self._llm = LLMRouter(self.cfg)
        return self._llm

    async def scrape(self, req: ScrapeRequest) -> ScrapeResponse:
        """Scrape single URL with optional LLM analysis."""
        start = time.time()

        # Use ProviderRouter
        from providers import ProviderRouter

        router = ProviderRouter(
            {
                "jina_api_key": self.cfg.jina_api_key,
                "scraperapi_key": self.cfg.scraperapi_key,
                "scrapingdog_key": self.cfg.scrapingdog_key,
                "firecrawl_api_key": self.cfg.firecrawl_api_key,
                "zenrows_key": self.cfg.zenrows_key,
                "ollama_model": self.cfg.ollama_model,
            }
        )

        result = await router.scrape(
            url=req.url,
            strategy=req.strategy,
            prompt=req.prompt,
            css_selector=req.css_selector,
        )

        resp = ScrapeResponse(
            url=result.url,
            markdown=result.markdown or "",
            text=result.text or "",
            html=result.html or "",
            title=getattr(result, "title", ""),
            links=getattr(result, "links", []),
            elements=[],
            provider=result.provider,
            cost_usd=result.cost_usd,
            elapsed_ms=round((time.time() - start) * 1000),
            error=result.error,
        )

        # LLM analysis if text available
        content = result.markdown or result.text or ""
        if content and not result.error:
            analysis = await self.llm.analyze(
                content,
                task=req.task,
                complexity=req.complexity,
            )
            resp.analysis = analysis.analysis or ""
            resp.model_used = analysis.model_used or ""
            resp.cost_usd += analysis.cost_usd or 0.0
            resp.elapsed_ms = round((time.time() - start) * 1000)
            if analysis.error and not resp.error:
                resp.error = f"LLM error: {analysis.error}"

        return resp

    async def scrape_bulk(
        self,
        urls: list[str],
        strategy: str = "smart",
        task: str = "summarize",
        complexity: str = "low",
        max_concurrent: int = 5,
    ) -> list[ScrapeResponse]:
        """Scrape multiple URLs concurrently."""
        import asyncio

        sem = asyncio.Semaphore(max_concurrent)

        async def bounded(url: str) -> ScrapeResponse:
            async with sem:
                req = ScrapeRequest(
                    url=url, strategy=strategy, task=task, complexity=complexity
                )
                return await self.scrape(req)

        results = await asyncio.gather(
            *[bounded(u) for u in urls], return_exceptions=True
        )
        out = []
        for i, r in enumerate(results):
            if isinstance(r, ScrapeResponse):
                out.append(r)
            else:
                out.append(ScrapeResponse(url=urls[i], error=str(r), elapsed_ms=0))
        return out
