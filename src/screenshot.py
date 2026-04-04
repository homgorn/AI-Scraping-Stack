"""
src/screenshot.py — Screenshot & page discovery service
=========================================================
Backends (in priority order, all free):
  1. Crawl4AI   — screenshot=True, PDF, full-page scroll, anti-bot v3
  2. Playwright  — direct, full-page, no extra deps if Crawl4AI installed
  3. Scrapling DynamicFetcher — fallback

Sitemap / robots.txt parsing:
  - robots.txt → disallowed paths, sitemap URLs
  - sitemap.xml (+ sitemap index) → all page URLs
  - Key page heuristics → /about /pricing /features /blog etc.

Usage:
    svc = ScreenshotService(settings)
    result = await svc.capture("https://example.com")
    # result.screenshot_b64  → base64 PNG
    # result.key_pages        → ["/about", "/pricing", ...]
    # result.sitemap_urls     → full list from sitemap
"""
import asyncio
import base64
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse
import httpx

from src.config import Settings


@dataclass
class ScreenshotResult:
    url: str
    screenshot_b64: str = ""           # PNG as base64
    screenshot_path: str = ""          # saved file path (if output_dir set)
    pdf_b64: str = ""                  # PDF as base64 (Crawl4AI only)
    width: int = 1440
    height: int = 900
    full_page: bool = True
    provider: str = "unknown"
    elapsed_ms: int = 0
    error: Optional[str] = None


@dataclass
class SiteMapResult:
    url: str
    robots_txt: str = ""
    sitemap_urls: list[str] = field(default_factory=list)   # from sitemap.xml
    key_pages: list[str] = field(default_factory=list)       # /about, /pricing etc
    disallowed: list[str] = field(default_factory=list)
    all_discovered_urls: list[str] = field(default_factory=list)
    error: Optional[str] = None


# Key page patterns to look for
KEY_PAGE_PATTERNS = [
    "/about", "/about-us", "/company", "/who-we-are",
    "/pricing", "/plans", "/price", "/cost",
    "/features", "/product", "/solutions",
    "/blog", "/news", "/articles", "/learn",
    "/contact", "/contact-us", "/get-started",
    "/demo", "/try", "/signup", "/register",
    "/docs", "/documentation", "/developers", "/api",
    "/cases", "/case-studies", "/testimonials", "/reviews",
    "/team", "/careers", "/jobs",
]


class ScreenshotService:
    """
    Unified screenshot service.
    Tries Crawl4AI → Playwright → Scrapling in order.
    All return ScreenshotResult with base64 PNG.
    """

    def __init__(self, settings: Settings):
        self.cfg = settings

    async def capture(
        self,
        url: str,
        width: int = 1440,
        height: int = 900,
        full_page: bool = True,
        output_dir: str = "",
        wait_for: str = "",
        pdf: bool = False,
    ) -> ScreenshotResult:
        """Capture screenshot of URL. Tries backends in order."""
        start = time.time()

        # Try Crawl4AI first (best: anti-bot, full-page scroll, PDF)
        result = await self._crawl4ai(url, width, height, full_page, pdf, wait_for)
        if result.error:
            # Fallback: raw Playwright
            result = await self._playwright(url, width, height, full_page)
        if result.error:
            # Last resort: Scrapling DynamicFetcher screenshot
            result = await self._scrapling(url, width, height)

        result.elapsed_ms = round((time.time() - start) * 1000)

        # Save to file if output_dir provided
        if output_dir and result.screenshot_b64:
            path = self._save_screenshot(result.screenshot_b64, url, output_dir)
            result.screenshot_path = str(path)

        return result

    async def capture_many(
        self,
        urls: list[str],
        max_concurrent: int = 3,
        output_dir: str = "",
        **kwargs,
    ) -> list[ScreenshotResult]:
        """Capture screenshots of multiple URLs concurrently."""
        sem = asyncio.Semaphore(max_concurrent)

        async def bounded(url: str) -> ScreenshotResult:
            async with sem:
                return await self.capture(url, output_dir=output_dir, **kwargs)

        results = await asyncio.gather(
            *[bounded(u) for u in urls], return_exceptions=True
        )
        return [
            r if isinstance(r, ScreenshotResult)
            else ScreenshotResult(url=urls[i], error=str(r))
            for i, r in enumerate(results)
        ]

    # ── Backends ──────────────────────────────────────────────────────────────

    async def _crawl4ai(
        self,
        url: str,
        width: int,
        height: int,
        full_page: bool,
        pdf: bool,
        wait_for: str,
    ) -> ScreenshotResult:
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode

            browser_cfg = BrowserConfig(
                headless=True,
                viewport_width=width,
                viewport_height=height,
            )
            run_cfg = CrawlerRunConfig(
                screenshot=True,
                pdf=pdf,
                cache_mode=CacheMode.BYPASS,
                wait_for=wait_for or None,
                # Full-page scroll to load lazy content
                scroll_delay=0.3,
            )

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                res = await crawler.arun(url=url, config=run_cfg)

            if res.success and res.screenshot:
                return ScreenshotResult(
                    url=url,
                    screenshot_b64=res.screenshot,   # already base64
                    pdf_b64=res.pdf or "",
                    width=width,
                    height=height,
                    full_page=full_page,
                    provider="crawl4ai",
                )
            return ScreenshotResult(url=url, provider="crawl4ai",
                                    error=res.error_message or "no screenshot")
        except ImportError:
            return ScreenshotResult(url=url, provider="crawl4ai",
                                    error="crawl4ai not installed")
        except Exception as e:
            return ScreenshotResult(url=url, provider="crawl4ai", error=str(e))

    async def _playwright(
        self,
        url: str,
        width: int,
        height: int,
        full_page: bool,
    ) -> ScreenshotResult:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": width, "height": height})
                await page.goto(url, wait_until="networkidle", timeout=30000)
                # Scroll to trigger lazy load
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                png_bytes = await page.screenshot(full_page=full_page)
                await browser.close()

            return ScreenshotResult(
                url=url,
                screenshot_b64=base64.b64encode(png_bytes).decode(),
                width=width,
                height=height,
                full_page=full_page,
                provider="playwright",
            )
        except ImportError:
            return ScreenshotResult(url=url, provider="playwright",
                                    error="playwright not installed")
        except Exception as e:
            return ScreenshotResult(url=url, provider="playwright", error=str(e))

    async def _scrapling(
        self,
        url: str,
        width: int,
        height: int,
    ) -> ScreenshotResult:
        """Scrapling DynamicFetcher — last resort."""
        try:
            from scrapling.fetchers import DynamicFetcher

            page = DynamicFetcher(
                headless=True,
                screenshot=True,
                viewport={"width": width, "height": height},
            ).fetch(url)

            if hasattr(page, "screenshot") and page.screenshot:
                b64 = (
                    base64.b64encode(page.screenshot).decode()
                    if isinstance(page.screenshot, bytes)
                    else page.screenshot
                )
                return ScreenshotResult(
                    url=url,
                    screenshot_b64=b64,
                    width=width,
                    height=height,
                    provider="scrapling",
                )
            return ScreenshotResult(url=url, provider="scrapling",
                                    error="DynamicFetcher returned no screenshot")
        except Exception as e:
            return ScreenshotResult(url=url, provider="scrapling", error=str(e))

    # ── Utils ─────────────────────────────────────────────────────────────────

    def _save_screenshot(self, b64: str, url: str, output_dir: str) -> Path:
        slug = re.sub(r"[^\w]", "_", urlparse(url).netloc)[:40]
        ts = int(time.time())
        path = Path(output_dir) / f"{slug}_{ts}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(b64))
        return path


class SiteMapService:
    """
    Discover site structure:
      - robots.txt   → disallowed paths + sitemap URLs
      - sitemap.xml  → all indexed URLs (handles sitemap index)
      - Key pages    → heuristic match of important pages
    """

    def __init__(self, settings: Settings):
        self.cfg = settings

    async def discover(self, url: str, max_sitemap_urls: int = 200) -> SiteMapResult:
        base = self._base_url(url)
        result = SiteMapResult(url=url)

        # 1. robots.txt
        robots_data = await self._fetch_robots(base)
        result.robots_txt = robots_data["text"]
        result.disallowed = robots_data["disallowed"]
        sitemap_urls_from_robots = robots_data["sitemaps"]

        # 2. Sitemap(s)
        sitemap_candidates = sitemap_urls_from_robots or [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/sitemap.xml.gz",
        ]

        all_page_urls: list[str] = []
        for sm_url in sitemap_candidates[:3]:
            urls = await self._fetch_sitemap(sm_url, max_sitemap_urls)
            all_page_urls.extend(urls)

        # Deduplicate
        seen: set[str] = set()
        unique_urls = []
        for u in all_page_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        result.sitemap_urls = unique_urls[:max_sitemap_urls]
        result.all_discovered_urls = result.sitemap_urls

        # 3. Key pages — match patterns + check sitemap
        result.key_pages = self._find_key_pages(base, result.sitemap_urls)

        return result

    # ── robots.txt ─────────────────────────────────────────────────────────────

    async def _fetch_robots(self, base: str) -> dict:
        out = {"text": "", "disallowed": [], "sitemaps": []}
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
                r = await c.get(f"{base}/robots.txt",
                                headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    text = r.text
                    out["text"] = text
                    for line in text.splitlines():
                        line = line.strip()
                        if line.lower().startswith("disallow:"):
                            path = line[9:].strip()
                            if path and path != "/":
                                out["disallowed"].append(path)
                        elif line.lower().startswith("sitemap:"):
                            sm = line[8:].strip()
                            if sm:
                                out["sitemaps"].append(sm)
        except Exception:
            pass
        return out

    # ── sitemap.xml ────────────────────────────────────────────────────────────

    async def _fetch_sitemap(
        self, url: str, max_urls: int, depth: int = 0
    ) -> list[str]:
        if depth > 2:
            return []
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    return []
                content = r.text

            urls: list[str] = []

            # Sitemap index → recurse
            if "<sitemapindex" in content:
                sub_sitemaps = re.findall(r"<loc>\s*(https?://[^\s<]+\.xml[^<]*)\s*</loc>",
                                          content, re.IGNORECASE)
                tasks = [self._fetch_sitemap(sm, max_urls // len(sub_sitemaps) + 1, depth + 1)
                         for sm in sub_sitemaps[:10]]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, list):
                        urls.extend(res)
            else:
                # Regular sitemap
                found = re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>",
                                   content, re.IGNORECASE)
                urls = [u for u in found if not u.endswith((".xml", ".xml.gz"))]

            return urls[:max_urls]
        except Exception:
            return []

    # ── Key page discovery ─────────────────────────────────────────────────────

    def _find_key_pages(self, base: str, sitemap_urls: list[str]) -> list[str]:
        """Find key pages from sitemap + heuristic patterns."""
        key: list[str] = []
        sitemap_paths = {urlparse(u).path.rstrip("/").lower() for u in sitemap_urls}

        for pattern in KEY_PAGE_PATTERNS:
            # Exact match
            if pattern in sitemap_paths or pattern + "/" in sitemap_paths:
                key.append(base + pattern)
                continue
            # Prefix match in sitemap
            if any(p.startswith(pattern) for p in sitemap_paths):
                key.append(base + pattern)

        # If nothing from sitemap, return heuristic list
        if not key:
            key = [base + p for p in KEY_PAGE_PATTERNS[:8]]

        return list(dict.fromkeys(key))[:15]   # deduplicate, max 15

    def _base_url(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"
