"""
src/synthesizer.py — URL(s) → Synthesized Website
===================================================
Pipeline:
  1. Scrape N URLs in parallel (via ProviderRouter)
  2. Deep-research: current trends for topic (Jina Search)
  3. Multi-agent analysis: extractor → ranker → synthesizer → coder
  4. Output: complete website code (HTML/CSS/JS or full-stack spec)

Usage:
    from src.synthesizer import WebSynthesizer
    result = await WebSynthesizer(settings, llm_router).run(
        urls=["https://..."],
        prompt="Build a SaaS landing page for AI scraping tool",
        output_format="html"   # or "react" | "fullstack_spec"
    )
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Literal

from src.config import Settings
from src.llm import LLMRouter


@dataclass
class SynthesisResult:
    prompt: str
    urls_processed: int
    code: str = ""
    html: str = ""
    spec: str = ""
    stack: str = ""
    insights: list[str] = field(default_factory=list)
    trends: list[str] = field(default_factory=list)
    elapsed_ms: int = 0
    cost_usd: float = 0.0
    error: str = ""


# ── Agent prompts ─────────────────────────────────────────────────────────────

EXTRACTOR_PROMPT = """You are a content extraction agent.
Extract the most valuable information from this web content.
Focus on: structure, UX patterns, key features, pricing, CTAs, value propositions.
Return as JSON: {{"title": str, "key_points": [str], "patterns": [str], "data": dict}}

Content:
{content}"""

RANKER_PROMPT = """You are a content ranking agent.
Given multiple pieces of web content analysis, rank and filter the most relevant insights.
Remove duplicates. Keep top insights. Identify common patterns and what makes pages successful.
Return JSON: {{"top_insights": [str], "common_patterns": [str], "best_practices": [str], "unique_ideas": [str]}}

Content analyses:
{analyses}"""

TREND_PROMPT = """You are a research agent. Today's date: {date}.
Based on this search data about "{topic}", identify:
- Current trends (2025-2026)
- Best practices right now
- What modern users expect
- Cutting-edge features to include
Return JSON: {{"trends": [str], "must_have_features": [str], "modern_stack": [str]}}

Search results:
{search_data}"""

ARCHITECT_PROMPT = """You are a senior web architect and UX designer.
Based on the research below, design a complete website for this request:

REQUEST: {prompt}

RESEARCH INSIGHTS:
{insights}

TRENDS:
{trends}

Design:
1. Information architecture
2. Key sections and their purpose
3. UX/UI approach
4. Technology stack recommendation
5. Key differentiators to include

Return JSON: {{
  "sections": [{{"name": str, "purpose": str, "content_notes": str}}],
  "stack": {{"frontend": str, "backend": str, "database": str, "deploy": str}},
  "ux_approach": str,
  "differentiators": [str],
  "color_scheme": str,
  "tone": str
}}"""

HTML_CODER_PROMPT = """You are an expert frontend developer.
Create a COMPLETE, production-ready single-page website.

DESIGN SPEC:
{spec}

USER REQUEST: {prompt}

Requirements:
- Modern design, not generic
- Mobile responsive
- Clean semantic HTML5
- Inline CSS (no external stylesheets needed)
- Vanilla JS or minimal dependencies from CDN only
- All sections from the spec
- Real placeholder content matching the topic
- Dark/light professional aesthetic

Return ONLY the complete HTML code starting with <!DOCTYPE html>.
No explanation, no markdown fences, just HTML."""

REACT_CODER_PROMPT = """You are an expert React developer.
Create a complete React application for this request.

DESIGN SPEC:
{spec}

USER REQUEST: {prompt}

Requirements:
- React 18 with hooks
- Tailwind CSS (CDN)
- Lucide icons
- Mobile responsive
- Production-ready component structure
- TypeScript types in JSDoc comments

Return ONLY the complete React component code."""

FULLSTACK_SPEC_PROMPT = """You are a senior software architect.
Create a complete full-stack project specification.

DESIGN SPEC:
{spec}

USER REQUEST: {prompt}

Produce a detailed spec including:
1. Project structure (directory tree)
2. Tech stack with versions
3. Database schema
4. API endpoints (REST or GraphQL)
5. Frontend architecture
6. Authentication approach
7. Deployment architecture
8. Docker compose config outline
9. Key implementation notes per module
10. Estimated dev time per module

Format as clean Markdown."""


class WebSynthesizer:
    """
    Multi-agent pipeline: N URLs → synthesized website.

    Agents:
        Extractor  → pulls structured data from each page
        Ranker     → finds best patterns across all pages
        Researcher → fetches current trends via Jina Search
        Architect  → designs site based on research + trends
        Coder      → generates complete code from architect spec
    """

    def __init__(self, settings: Settings, llm: LLMRouter):
        self.cfg = settings
        self.llm = llm

    async def run(
        self,
        urls: list[str],
        prompt: str,
        output_format: Literal["html", "react", "fullstack_spec"] = "html",
        research_trends: bool = True,
        complexity: Literal["low", "medium", "high"] = "high",
    ) -> SynthesisResult:
        start = time.time()
        result = SynthesisResult(prompt=prompt, urls_processed=len(urls))

        # ── Step 1: Scrape all URLs in parallel ───────────────────────────────
        scraped_contents = await self._scrape_all(urls)
        if not scraped_contents:
            result.error = "All URLs failed to scrape"
            return result

        # ── Step 2: Extract insights from each page (parallel) ────────────────
        extractions = await self._extract_all(scraped_contents, complexity)

        # ── Step 3: Research current trends ───────────────────────────────────
        trends_data: list[str] = []
        if research_trends:
            trends_data = await self._research_trends(prompt, complexity)
            result.trends = trends_data

        # ── Step 4: Rank + synthesize all extractions ─────────────────────────
        insights = await self._rank_insights(extractions, complexity)
        result.insights = insights

        # ── Step 5: Architect the site ────────────────────────────────────────
        spec_json = await self._architect(prompt, insights, trends_data, complexity)
        result.spec = json.dumps(spec_json, ensure_ascii=False, indent=2)
        result.stack = spec_json.get("stack", {}).get("frontend", "HTML/CSS/JS")

        # ── Step 6: Code generation ───────────────────────────────────────────
        code = await self._generate_code(prompt, spec_json, output_format, complexity)
        result.code = code
        if output_format == "html":
            result.html = code

        result.elapsed_ms = round((time.time() - start) * 1000)
        return result

    async def run_multi_output(
        self,
        urls: list[str],
        prompt: str,
        num_variants: int = 2,
    ) -> list[SynthesisResult]:
        """Generate multiple website variants from same research."""
        formats: list[Literal["html", "react", "fullstack_spec"]] = [
            "html",
            "react",
            "fullstack_spec",
        ]
        chosen = formats[:num_variants]

        # Scrape + research once, generate multiple outputs
        scraped = await self._scrape_all(urls)
        extractions = await self._extract_all(scraped, "high")
        trends = await self._research_trends(prompt, "high")
        insights = await self._rank_insights(extractions, "high")
        spec_json = await self._architect(prompt, insights, trends, "high")

        results = []
        for fmt in chosen:
            code = await self._generate_code(prompt, spec_json, fmt, "high")
            r = SynthesisResult(
                prompt=prompt,
                urls_processed=len(urls),
                spec=json.dumps(spec_json, indent=2),
                code=code,
                insights=insights,
                trends=trends,
                stack=fmt,
            )
            if fmt == "html":
                r.html = code
            results.append(r)
        return results

    # ── Private pipeline steps ────────────────────────────────────────────────

    async def _scrape_all(self, urls: list[str]) -> list[str]:
        """Scrape URLs, return list of text content."""
        try:
            from providers import ProviderRouter

            router = ProviderRouter(
                {
                    "jina_api_key": self.cfg.jina_api_key,
                    "scraperapi_key": self.cfg.scraperapi_key,
                }
            )
            sem = asyncio.Semaphore(5)

            async def scrape_one(url: str) -> str:
                async with sem:
                    r = await router.scrape(url, strategy="free")
                    return r.markdown or r.text or ""

            results = await asyncio.gather(
                *[scrape_one(u) for u in urls], return_exceptions=True
            )
            return [r for r in results if isinstance(r, str) and len(r) > 100]
        except ImportError:
            return []

    async def _extract_all(self, contents: list[str], complexity: str) -> list[str]:
        """Run extractor agent on each scraped page."""
        sem = asyncio.Semaphore(3)

        async def extract_one(content: str) -> str:
            async with sem:
                prompt = EXTRACTOR_PROMPT.format(content=content[:3000])
                r = await self.llm.analyze(
                    prompt,
                    task="custom:" + prompt,
                    complexity=complexity,  # type: ignore
                )
                return r.analysis

        results = await asyncio.gather(
            *[extract_one(c) for c in contents], return_exceptions=True
        )
        return [r for r in results if isinstance(r, str) and len(r) > 20]

    async def _research_trends(self, topic: str, complexity: str) -> list[str]:
        """Fetch current trends via Jina Search."""
        import httpx
        from datetime import datetime

        search_results = []
        queries = [
            f"{topic} best practices 2026",
            f"{topic} trends modern design",
            f"top {topic} websites examples",
        ]

        for q in queries[:2]:  # limit to 2 searches
            try:
                headers = {}
                if self.cfg.jina_api_key:
                    headers["Authorization"] = f"Bearer {self.cfg.jina_api_key}"
                async with httpx.AsyncClient(timeout=20) as c:
                    r = await c.get(
                        f"https://s.jina.ai/{q.replace(' ', '+')}",
                        headers=headers,
                    )
                    if r.status_code == 200:
                        search_results.append(r.text[:2000])
            except Exception:
                pass

        if not search_results:
            return ["No trend data available — proceed with best practices"]

        combined = "\n---\n".join(search_results)
        trend_prompt = TREND_PROMPT.format(
            date=datetime.now().strftime("%B %Y"),
            topic=topic,
            search_data=combined[:4000],
        )
        r = await self.llm.analyze(
            trend_prompt,
            task="custom:" + trend_prompt,
            complexity=complexity,  # type: ignore
        )
        try:
            data = json.loads(r.analysis)
            trends = data.get("trends", []) + data.get("must_have_features", [])
            return trends[:10]
        except Exception:
            return [r.analysis[:500]]

    async def _rank_insights(
        self, extractions: list[str], complexity: str
    ) -> list[str]:
        """Rank and deduplicate insights from all extractions."""
        combined = "\n\n---\n\n".join(extractions[:10])
        rank_prompt = RANKER_PROMPT.format(analyses=combined[:5000])
        r = await self.llm.analyze(
            rank_prompt,
            task="custom:" + rank_prompt,
            complexity=complexity,  # type: ignore
        )
        try:
            data = json.loads(r.analysis)
            return (
                data.get("top_insights", [])
                + data.get("best_practices", [])
                + data.get("unique_ideas", [])
            )[:15]
        except Exception:
            return [r.analysis[:1000]]

    async def _architect(
        self, prompt: str, insights: list[str], trends: list[str], complexity: str
    ) -> dict:
        """Design site architecture."""
        arch_prompt = ARCHITECT_PROMPT.format(
            prompt=prompt,
            insights="\n".join(f"- {i}" for i in insights),
            trends="\n".join(f"- {t}" for t in trends),
        )
        r = await self.llm.analyze(
            arch_prompt,
            task="custom:" + arch_prompt,
            complexity=complexity,  # type: ignore
        )
        try:
            # Strip markdown fences if present
            text = r.analysis.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception:
            return {
                "sections": [{"name": "Main", "purpose": "Landing"}],
                "stack": {"frontend": "HTML/CSS/JS"},
                "ux_approach": r.analysis[:500],
                "differentiators": [],
                "color_scheme": "dark professional",
                "tone": "modern",
            }

    async def _generate_code(
        self,
        prompt: str,
        spec: dict,
        output_format: str,
        complexity: str,
    ) -> str:
        """Generate final code from architecture spec."""
        spec_str = json.dumps(spec, ensure_ascii=False, indent=2)

        if output_format == "react":
            code_prompt = REACT_CODER_PROMPT.format(spec=spec_str, prompt=prompt)
        elif output_format == "fullstack_spec":
            code_prompt = FULLSTACK_SPEC_PROMPT.format(spec=spec_str, prompt=prompt)
        else:
            code_prompt = HTML_CODER_PROMPT.format(spec=spec_str, prompt=prompt)

        r = await self.llm.analyze(
            code_prompt,
            task="custom:" + code_prompt,
            complexity=complexity,  # type: ignore
        )
        code = r.analysis.strip()
        # Strip markdown fences from code response
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return code
