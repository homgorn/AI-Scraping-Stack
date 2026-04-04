"""
src/llm.py — LLM Router: Ollama (local) + OpenRouter (cloud)
=============================================================
Smart routing:
  low    → Ollama local (free, private)
  medium → OpenRouter free tier (Qwen3, Llama3.3)
  high   → OpenRouter configured model (Claude, GPT-4o)

Usage:
    from src.llm import LLMRouter
    from src.config import get_settings
    llm = LLMRouter(get_settings())
    result = await llm.analyze("text", task="summarize", complexity="low")
"""

import time
from typing import Literal, Optional

import httpx

from src.config import Settings
from src.models import AnalyzeResponse

# ── Task prompts ──────────────────────────────────────────────────────────────

TASK_PROMPTS: dict[str, str] = {
    "summarize": "Summarize this text concisely in 3-5 sentences:\n\n{text}",
    "extract_entities": "Extract all named entities (people, orgs, products, dates, prices) as JSON:\n\n{text}",
    "classify": "Classify this content into one category (news/product/blog/docs/ecommerce/other). Return only the label:\n\n{text}",
    "extract_prices": "Extract all prices as JSON array of {{name, price, currency}}:\n\n{text}",
    "sentiment": "Analyze sentiment. Return JSON: {{positive, negative, neutral, label}}:\n\n{text}",
    "extract_links": "Extract all links as JSON array of {{url, text}}:\n\n{text}",
    "translate_ru": "Translate this text to Russian:\n\n{text}",
    "translate_en": "Translate this text to English:\n\n{text}",
}


class LLMRouter:
    """Routes LLM calls between Ollama (local) and OpenRouter (cloud)."""

    def __init__(self, settings: Settings):
        self.cfg = settings

    async def analyze(
        self,
        text: str,
        task: str = "summarize",
        complexity: Literal["low", "medium", "high"] = "low",
        model_override: str = "",
        model_source: Literal["auto", "ollama", "openrouter"] = "auto",
    ) -> AnalyzeResponse:
        """Analyze text with smart routing."""
        start = time.time()
        prompt = self._build_prompt(text, task)

        # Override source
        if model_source == "ollama":
            return await self._call_ollama(prompt, model_override, start)
        if model_source == "openrouter":
            return await self._call_openrouter(
                prompt, complexity, model_override, start
            )

        # Auto routing
        if complexity == "low":
            result = await self._call_ollama(prompt, model_override, start)
            if result.error and self.cfg.openrouter_api_key:
                return await self._call_openrouter(
                    prompt, "medium", model_override, start
                )
            return result

        return await self._call_openrouter(prompt, complexity, model_override, start)

    def _build_prompt(self, text: str, task: str) -> str:
        if task.startswith("qa:"):
            question = task[3:]
            return f"Answer this question based on the text.\nQ: {question}\n\nText:\n{text[:8000]}"
        if task.startswith("custom:"):
            return task[7:]
        template = TASK_PROMPTS.get(task, TASK_PROMPTS["summarize"])
        return template.format(text=text[:8000])

    async def _call_ollama(
        self, prompt: str, model_override: str, start: float
    ) -> AnalyzeResponse:
        model = model_override or self.cfg.ollama_model
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
                    f"{self.cfg.ollama_host}/api/chat",
                    json={
                        "model": model,
                        "stream": False,
                        "messages": [{"role": "user", "content": prompt}],
                        "options": {
                            "temperature": self.cfg.llm_temperature,
                            "num_predict": self.cfg.llm_max_tokens,
                        },
                    },
                )
                r.raise_for_status()
                data = r.json()
                return AnalyzeResponse(
                    analysis=data["message"]["content"],
                    model_used=f"ollama/{model}",
                    elapsed_ms=round((time.time() - start) * 1000),
                )
        except Exception as e:
            return AnalyzeResponse(
                analysis="",
                model_used=f"ollama/{model}",
                elapsed_ms=round((time.time() - start) * 1000),
                error=str(e),
            )

    async def _call_openrouter(
        self,
        prompt: str,
        complexity: str,
        model_override: str,
        start: float,
    ) -> AnalyzeResponse:
        if not self.cfg.openrouter_api_key:
            return AnalyzeResponse(
                analysis="",
                model_used="",
                elapsed_ms=0,
                error="OpenRouter API key not set",
            )

        model = model_override or self._resolve_model(complexity)
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
                    f"{self.cfg.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.cfg.openrouter_api_key}",
                        "HTTP-Referer": self.cfg.openrouter_site_url,
                        "X-Title": self.cfg.openrouter_app_name,
                    },
                    json={
                        "model": model,
                        "max_tokens": self.cfg.llm_max_tokens,
                        "temperature": self.cfg.llm_temperature,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                cost = data.get("usage", {})
                return AnalyzeResponse(
                    analysis=content,
                    model_used=f"openrouter/{model}",
                    elapsed_ms=round((time.time() - start) * 1000),
                    cost_usd=cost.get("total_cost", 0.0),
                )
        except Exception as e:
            return AnalyzeResponse(
                analysis="",
                model_used=f"openrouter/{model}",
                elapsed_ms=round((time.time() - start) * 1000),
                error=str(e),
            )

    def _resolve_model(self, complexity: str) -> str:
        if complexity == "low":
            return "meta-llama/llama-3.2-3b-instruct:free"
        if complexity == "medium":
            return "qwen/qwen3-30b-a3b:free"
        return self.cfg.openrouter_model

    async def list_ollama_models(self) -> list[str]:
        """Get installed Ollama models."""
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self.cfg.ollama_host}/api/tags")
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    async def pull_ollama_model(self, model_name: str) -> AsyncIterator[str]:
        """Pull Ollama model with streaming progress."""
        async with httpx.AsyncClient(timeout=600) as c:
            async with c.stream(
                "POST",
                f"{self.cfg.ollama_host}/api/pull",
                json={"name": model_name, "stream": True},
            ) as r:
                async for line in r.aiter_lines():
                    if line:
                        yield line
