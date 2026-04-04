"""
4-Layer AI Scraping Stack
=========================
Layer 1: Scrapling v0.4  — fetching + anti-bot bypass + adaptive parser
Layer 2: Ollama           — local LLM (Llama3.2 / Mistral) for analysis
Layer 3: MCP Server       — Scrapling exposed as MCP tools for agents
Layer 4: OpenRouter SDK   — cloud LLM fallback / routing (300+ models)

Install:
    pip install "scrapling[ai,fetchers]" ollama openai instructor pydantic python-dotenv
    scrapling install
    ollama pull llama3.2
"""

import os
import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

# ─────────────────────────────────────────────
# LAYER 1: SCRAPLING  (fetching + parsing)
# ─────────────────────────────────────────────
try:
    from scrapling.fetchers import (
        Fetcher,
        AsyncFetcher,
        StealthyFetcher,
        DynamicFetcher,
    )
    from scrapling import Adaptor

    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    Fetcher = AsyncFetcher = StealthyFetcher = DynamicFetcher = None
    Adaptor = None


@dataclass
class ScrapeResult:
    url: str
    html: str = ""
    markdown: str = ""
    text: str = ""
    structured: dict = field(default_factory=dict)
    error: Optional[str] = None


class Layer1_Scraper:
    """
    Scrapling v0.4 — adaptive web scraping with anti-bot bypass.
    Three fetcher modes:
      - fast:    Fetcher()         → HTTP + browser headers spoofing
      - stealth: StealthyFetcher() → Playwright + Cloudflare bypass
      - dynamic: DynamicFetcher()  → full Chromium, JS-heavy pages
    """

    def fetch(
        self,
        url: str,
        mode: Literal["fast", "stealth", "dynamic"] = "fast",
        css_selector: Optional[str] = None,
        adaptive: bool = False,
        proxy: Optional[str] = None,
    ) -> ScrapeResult:
        result = ScrapeResult(url=url)
        try:
            kwargs = {}
            if proxy:
                kwargs["proxy"] = proxy

            if mode == "fast":
                page = Fetcher().get(url, **kwargs)
            elif mode == "stealth":
                # StealthyFetcher — обходит Cloudflare Turnstile
                StealthyFetcher.adaptive = adaptive
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, **kwargs)
            else:  # dynamic
                page = DynamicFetcher().fetch(url, **kwargs)

            result.html = page.html
            # Scrapling built-in markdown extraction
            result.text = page.get_all_text(ignore_tags=["script", "style"])

            if css_selector:
                elements = page.css(
                    css_selector,
                    auto_save=True,  # сохраняем fingerprint для adaptive
                )
                result.structured["elements"] = [el.text for el in elements if el.text]

        except Exception as e:
            result.error = str(e)

        return result

    async def bulk_fetch(self, urls: list[str], mode: Literal["fast", "stealth"] = "fast") -> list[ScrapeResult]:
        """Параллельный fetch нескольких URL одновременно"""
        if mode == "fast":
            pages = await AsyncFetcher().batch(urls)
        else:
            pages = await StealthyFetcher.async_batch(urls, headless=True)

        results = []
        for url, page in zip(urls, pages):
            r = ScrapeResult(url=url)
            if page:
                r.html = page.html
                r.text = page.get_all_text(ignore_tags=["script", "style"])
            results.append(r)
        return results


# ─────────────────────────────────────────────
# LAYER 2: OLLAMA  (local LLM analysis)
# ─────────────────────────────────────────────
try:
    import ollama as _ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    _ollama = None
    OLLAMA_AVAILABLE = False


class Layer2_LocalLLM:
    """
    Ollama — запуск LLM на своей машине.
    Нет запросов к OpenAI, нет счёта за токены.
    Модели: llama3.2, mistral, qwen2.5, etc.
    """

    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST):
        self.client = _ollama.Client(host=host)
        self.model = model

    def analyze(self, text: str, task: str = "summarize") -> str:
        """
        task: "summarize" | "extract_entities" | "classify" | "qa:<question>"
        """
        prompts = {
            "summarize": (f"Summarize this text concisely in 3-5 sentences:\n\n{text[:4000]}"),
            "extract_entities": (
                f"Extract all named entities (people, orgs, products, dates, prices) as JSON list:\n\n{text[:4000]}"
            ),
            "classify": (f"Classify this content into one category (news/product/blog/docs/other):\n\n{text[:2000]}"),
        }

        if task.startswith("qa:"):
            question = task[3:]
            prompt = f"Answer this question based on the text.\nQ: {question}\n\nText:\n{text[:4000]}"
        else:
            prompt = prompts.get(task, prompts["summarize"])

        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    def extract_structured(self, text: str, schema: dict) -> dict:
        """Извлечение структурированных данных под произвольную JSON-схему"""
        prompt = (
            f"Extract data from the text into this JSON schema.\n"
            f"Return ONLY valid JSON, no explanation.\n"
            f"Schema: {json.dumps(schema)}\n\n"
            f"Text:\n{text[:4000]}"
        )
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response["message"]["content"].strip()
        # strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}


# ─────────────────────────────────────────────
# LAYER 4: OPENROUTER SDK  (cloud LLM fallback)
# ─────────────────────────────────────────────
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False


class Layer4_OpenRouter:
    """
    OpenRouter — единый API для 300+ LLM-моделей.
    Используется как fallback когда:
      - Ollama не справляется со сложным заданием
      - Нужна мощная модель (Claude, GPT-4o, Gemini)
      - Бесплатные модели (Qwen, Llama3 на OpenRouter free tier)

    Совместим с OpenAI SDK (base_url override).
    """

    FREE_MODELS = [
        "qwen/qwen3-30b-a3b:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemma-3-27b-it:free",
    ]

    def __init__(self, api_key: str = OPENROUTER_API_KEY):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://your-app.com",
                "X-Title": "AI Scraping Stack",
            },
        )

    def analyze(
        self,
        text: str,
        task: str = "summarize",
        model: str = OPENROUTER_MODEL,
        use_free: bool = False,
    ) -> str:
        if use_free:
            model = self.FREE_MODELS[0]

        system_prompts = {
            "summarize": "You are a content analyst. Summarize concisely.",
            "extract": "You are a data extractor. Return only valid JSON.",
            "classify": "You are a classifier. Return single category label.",
        }

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompts.get(task, system_prompts["summarize"]),
                },
                {"role": "user", "content": text[:8000]},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content

    def route(
        self,
        text: str,
        task: str,
        complexity: Literal["low", "medium", "high"] = "medium",
    ) -> str:
        """
        Smart routing:
          low    → Llama3 free tier  (быстро, бесплатно)
          medium → Mistral Nemo      (баланс)
          high   → Claude Sonnet     (качество)
        """
        routing = {
            "low": "meta-llama/llama-3.2-3b-instruct:free",
            "medium": "mistralai/mistral-nemo:free",
            "high": "anthropic/claude-3.5-sonnet",
        }
        return self.analyze(text, task, model=routing[complexity])


# ─────────────────────────────────────────────
# ORCHESTRATOR — склеивает все 4 слоя
# ─────────────────────────────────────────────
class ScrapingOrchestrator:
    """
    Главный класс — оркестрирует 4 слоя в единый пайплайн.

    Логика:
    1. Scrapling получает страницу (адаптивно, anti-bot)
    2. Ollama анализирует контент локально (экономия)
    3. OpenRouter подключается только для сложных задач
    4. MCP Server делает всё это доступным AI-агентам как tools
    """

    def __init__(
        self,
        use_openrouter: bool = True,
        local_only: bool = False,
    ):
        self.scraper = Layer1_Scraper()
        self.local_llm = Layer2_LocalLLM()
        self.openrouter = Layer4_OpenRouter() if use_openrouter else None
        self.local_only = local_only

    def scrape_and_analyze(
        self,
        url: str,
        task: str = "summarize",
        fetch_mode: Literal["fast", "stealth", "dynamic"] = "fast",
        css_selector: Optional[str] = None,
        complexity: Literal["low", "medium", "high"] = "low",
    ) -> dict:
        """
        Полный пайплайн: URL → структурированный результат с анализом
        """
        # Step 1: Fetch
        scraped = self.scraper.fetch(url, mode=fetch_mode, css_selector=css_selector)
        if scraped.error:
            return {"error": scraped.error, "url": url}

        # Step 2: Local LLM analysis
        content = scraped.text[:4000] if scraped.text else ""
        local_result = self.local_llm.analyze(content, task=task)

        result = {
            "url": url,
            "fetch_mode": fetch_mode,
            "text_length": len(scraped.text),
            "local_analysis": local_result,
            "structured_elements": scraped.structured.get("elements", []),
        }

        # Step 3: OpenRouter fallback for complex tasks
        if not self.local_only and self.openrouter and complexity in ("medium", "high"):
            cloud_result = self.openrouter.route(content, task, complexity)
            result["cloud_analysis"] = cloud_result

        return result

    async def bulk_scrape_and_analyze(self, urls: list[str], task: str = "summarize") -> list[dict]:
        """Параллельный scrape + анализ нескольких URL"""
        scraped_list = await self.scraper.bulk_fetch(urls)
        results = []
        for scraped in scraped_list:
            if scraped.error:
                results.append({"url": scraped.url, "error": scraped.error})
                continue
            analysis = self.local_llm.analyze(scraped.text[:3000], task=task)
            results.append(
                {
                    "url": scraped.url,
                    "analysis": analysis,
                    "text_length": len(scraped.text),
                }
            )
        return results


# ─────────────────────────────────────────────
# LAYER 3: MCP SERVER (Scrapling as MCP tools)
# ─────────────────────────────────────────────
# NOTE: Scrapling v0.4 имеет ВСТРОЕННЫЙ MCP server!
# Запуск: scrapling mcp
# или:    scrapling mcp --http --host 0.0.0.0 --port 8000
#
# Конфиг для Claude Desktop (~/.claude/mcp_config.json):
# {
#   "mcpServers": {
#     "ScraplingServer": {
#       "command": "scrapling",
#       "args": ["mcp"]
#     }
#   }
# }
#
# Ниже — расширенный MCP server через FastMCP
# с интеграцией Ollama + OpenRouter поверх Scrapling:

try:
    from fastmcp import FastMCP

    mcp = FastMCP("AI Scraping Stack")

    _orchestrator = ScrapingOrchestrator()

    @mcp.tool()
    def scrape_and_analyze_url(
        url: str,
        task: str = "summarize",
        fetch_mode: str = "fast",
        css_selector: str = "",
        complexity: str = "low",
    ) -> dict:
        """
        Scrape a URL and analyze its content with AI.
        fetch_mode: fast | stealth | dynamic
        task: summarize | extract_entities | classify | qa:<question>
        complexity: low (Ollama) | medium (Mistral) | high (Claude)
        """
        return _orchestrator.scrape_and_analyze(
            url=url,
            task=task,
            fetch_mode=fetch_mode,  # type: ignore
            css_selector=css_selector or None,
            complexity=complexity,  # type: ignore
        )

    @mcp.tool()
    def quick_extract(url: str, css_selector: str) -> list[str]:
        """Extract specific elements from a URL using CSS selector."""
        result = _orchestrator.scraper.fetch(url, css_selector=css_selector, mode="fast")
        return result.structured.get("elements", [])

    @mcp.tool()
    def stealth_fetch(url: str, question: str = "") -> str:
        """
        Fetch a bot-protected page using StealthyFetcher (Cloudflare bypass).
        Optionally answer a specific question about the content.
        """
        result = _orchestrator.scraper.fetch(url, mode="stealth")
        if result.error:
            return f"Error: {result.error}"
        if question:
            return _orchestrator.local_llm.analyze(result.text, task=f"qa:{question}")
        return result.text[:3000]

    MCP_AVAILABLE = True

except ImportError:
    MCP_AVAILABLE = False
    print("fastmcp not installed — MCP server disabled. pip install fastmcp")


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== AI Scraping Stack Demo ===\n")

    orch = ScrapingOrchestrator(use_openrouter=bool(OPENROUTER_API_KEY))

    # 1. Fast scrape + local LLM
    print("1. Fast scrape + Ollama analysis:")
    result = orch.scrape_and_analyze(
        url="https://example.com",
        task="summarize",
        fetch_mode="fast",
        complexity="low",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 2. MCP server (run separately)
    if MCP_AVAILABLE:
        print("\n2. MCP server available. Run with:")
        print("   scrapling mcp           # built-in Scrapling MCP")
        print("   python stack.py serve   # extended MCP with Ollama+OR")
    else:
        print("\n2. Install fastmcp for MCP server support")

    # 3. Start MCP server if requested
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve" and MCP_AVAILABLE:
        print("\nStarting MCP server...")
        mcp.run()
