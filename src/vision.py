"""
src/vision.py — Vision LLM analysis (updated March 2026)
===========================================================
Backends (free tier):
  1. Ollama local       — qwen3-vl:30b, qwen2.5vl:7b, llava, moondream
  2. OpenRouter free    — Qwen3-VL-235B thinking, NVIDIA Nemotron Nano 2 VL,
                          Kimi-VL, Qwen2.5-VL-72B, Llama 3.2 11B Vision
  3. HF Inference Router — router.huggingface.co (OpenAI-compat, free ~200/day)
  4. Custom endpoint    — any OpenAI-compatible vision API

Model Registry (data/vision_models.json):
  - Built-in: current OR free + HF + Ollama defaults
  - Custom: user-added, persisted
  - Auto-refresh: OR /api/v1/models at startup (vision-capable only)

Sources (verified March 30, 2026):
  openrouter.ai/collections/vision-models
  openrouter.ai/collections/free-models
  ollama.com/library/qwen3-vl
  huggingface.co/docs/inference-providers
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import httpx

from src.config import Settings


# ── Current free vision models (verified March 2026) ─────────────────────────

OPENROUTER_FREE_VISION: list[dict] = [
    {"id": "qwen/qwen3-vl-235b-a22b-thinking:free",
     "name": "Qwen3-VL 235B Thinking",
     "provider": "openrouter", "free": True, "context": 32768,
     "notes": "Best free VLM. MoE 235B, design→code, spatial reasoning, OCR."},
    {"id": "qwen/qwen3-vl-30b-a3b:free",
     "name": "Qwen3-VL 30B",
     "provider": "openrouter", "free": True, "context": 32768,
     "notes": "30B MoE, 3B active. Fast, great for bulk analysis."},
    {"id": "nvidia/nemotron-nano-2-vl-12b:free",
     "name": "NVIDIA Nemotron Nano 2 VL 12B",
     "provider": "openrouter", "free": True, "context": 32768,
     "notes": "#1 OCRBench v2. Mamba-Transformer hybrid. Charts, docs, receipts."},
    {"id": "moonshotai/kimi-vl-a3b-thinking:free",
     "name": "Kimi-VL A3B Thinking",
     "provider": "openrouter", "free": True, "context": 131072,
     "notes": "131K context. Native multimodal, visual coding."},
    {"id": "qwen/qwen2.5-vl-72b-instruct:free",
     "name": "Qwen2.5-VL 72B",
     "provider": "openrouter", "free": True, "context": 32768,
     "notes": "Stable fallback. Document analysis, structured extraction."},
    {"id": "qwen/qwen2.5-vl-32b-instruct:free",
     "name": "Qwen2.5-VL 32B",
     "provider": "openrouter", "free": True, "context": 32768,
     "notes": "Faster than 72B. Good accuracy/speed tradeoff."},
    {"id": "meta-llama/llama-3.2-11b-vision-instruct:free",
     "name": "Llama 3.2 11B Vision",
     "provider": "openrouter", "free": True, "context": 128000,
     "notes": "Meta. Reliable generalist. 128K context."},
    {"id": "mistralai/mistral-small-3.1-24b-instruct:free",
     "name": "Mistral Small 3.1 24B",
     "provider": "openrouter", "free": True, "context": 128000,
     "notes": "24B vision. Good structured extraction."},
    {"id": "google/gemma-3-27b-it:free",
     "name": "Gemma 3 27B",
     "provider": "openrouter", "free": True, "context": 131072,
     "notes": "Google. Multilingual. 131K context."},
    {"id": "openrouter/auto",
     "name": "OR Auto (picks best free)",
     "provider": "openrouter", "free": True, "context": 200000,
     "notes": "Auto-selects best available free model. Easiest option."},
]

OLLAMA_VISION_MODELS: list[dict] = [
    {"id": "qwen3-vl:30b",     "name": "Qwen3-VL 30B",
     "pull": "ollama pull qwen3-vl:30b",  "size_gb": 19.0, "vram_gb": 20,
     "provider": "ollama",
     "notes": "Best local VLM 2026. Design→code. Apache 2.0. Need 20GB VRAM."},
    {"id": "qwen3-vl",         "name": "Qwen3-VL 7B",
     "pull": "ollama pull qwen3-vl",       "size_gb": 4.9,  "vram_gb": 6,
     "provider": "ollama",
     "notes": "Compact Qwen3-VL. Good quality/VRAM ratio."},
    {"id": "qwen2.5vl:7b",    "name": "Qwen2.5-VL 7B",
     "pull": "ollama pull qwen2.5vl:7b",   "size_gb": 4.7,  "vram_gb": 6,
     "provider": "ollama",
     "notes": "Stable, well-tested. Screenshot QA, document analysis."},
    {"id": "llava:13b",        "name": "LLaVA 13B",
     "pull": "ollama pull llava:13b",       "size_gb": 8.0,  "vram_gb": 10,
     "provider": "ollama",
     "notes": "Classic reliable. UI description, captioning."},
    {"id": "llava:7b",         "name": "LLaVA 7B",
     "pull": "ollama pull llava:7b",        "size_gb": 4.7,  "vram_gb": 6,
     "provider": "ollama",
     "notes": "Lightweight generalist. Fast inference."},
    {"id": "moondream",        "name": "Moondream 1.7B",
     "pull": "ollama pull moondream",       "size_gb": 0.83, "vram_gb": 1.5,
     "provider": "ollama",
     "notes": "829MB. CPU-runnable. Quick descriptions only."},
    {"id": "llava-phi3",       "name": "LLaVA Phi-3",
     "pull": "ollama pull llava-phi3",      "size_gb": 2.9,  "vram_gb": 4,
     "provider": "ollama",
     "notes": "Microsoft Phi-3 based. Efficient."},
]

HF_VISION_MODELS: list[dict] = [
    {"id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
     "hf_id": "Qwen/Qwen3-VL-30B-A3B-Instruct",
     "name": "Qwen3-VL 30B (HF)",
     "provider": "huggingface",
     "notes": "Via HF Inference Providers. ~200 req/day free."},
    {"id": "meta-llama/Llama-3.2-11B-Vision-Instruct",
     "hf_id": "meta-llama/Llama-3.2-11B-Vision-Instruct",
     "name": "Llama 3.2 11B Vision (HF)",
     "provider": "huggingface",
     "notes": "Free on HF router.huggingface.co"},
    {"id": "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
     "hf_id": "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
     "name": "Mistral Small 3.1 24B Vision (HF)",
     "provider": "huggingface",
     "notes": "Via HF Inference Providers."},
]

# ── Vision task prompts ───────────────────────────────────────────────────────

VISION_TASKS: dict[str, str] = {
    "business_intel": 'Analyze this website screenshot. Return JSON only:\n{"company":"name","description":"what they do in 2 sentences","audience":"target customer","value_props":["3-5 props"],"pricing_model":"free/freemium/paid/enterprise/unknown","cta":"main CTA text","business_model":"SaaS/ecommerce/media/services/other","stage":"startup/scaleup/enterprise/unknown"}',
    "design_audit": 'Analyze as UX/UI designer. Return JSON only:\n{"layout":"grid/split/centered/asymmetric","color_scheme":"colors and mood","typography":"font observations","sections":["visible sections top-bottom"],"design_quality":"professional/amateur/mixed + why","modern_score":1-10,"trust_signals":["visible elements"],"improvements":["top 3 improvements"]}',
    "competitor_analysis": 'Extract competitive intelligence. Return JSON only:\n{"product":"core offering","usps":["unique selling points"],"pricing_tier":"free/freemium/paid/enterprise","tech_signals":["stack hints"],"tone":"formal/casual/technical","segment":"consumer/SMB/enterprise/developer","strengths":["what they do well"],"weaknesses":["gaps or missing elements"]}',
    "tech_stack": 'Identify technology signals. Return JSON only:\n{"framework_guess":"React/Vue/Next.js/other","ui_library":"Tailwind/Material/Bootstrap/custom","chat_widget":"Intercom/Drift/Crisp/none/unknown","analytics":"GA/Mixpanel/Segment/unknown","hosting":"Vercel/Netlify/AWS/Cloudflare/unknown","cms":"WordPress/Webflow/none","ecommerce":"Shopify/WooCommerce/custom/none","confidence":"low/medium/high"}',
    "ux_patterns": 'Identify UX patterns. Return JSON only:\n{"nav_pattern":"top-bar/sidebar/hamburger","hero_pattern":"text-image/video-bg/full-width/split","social_proof":["visible proof elements"],"cta_pattern":"button/banner/sticky/inline","trust_signals":["SSL/payments/certs visible"],"content_layout":"cards/list/grid/masonry","unique_patterns":["innovative UI elements"]}',
    "ocr_extract": "Extract ALL visible text from this screenshot with high accuracy. Preserve structure. Use section labels: [NAV] [HERO] [FEATURES] [PRICING] [TESTIMONIALS] [FOOTER]. Include button labels, nav items, and all copy.",
    "content_extract": "Extract all visible content organized by page section. Include headlines, body text, button labels, feature names, pricing. Format as Markdown with ## Section Headers.",
    "summary": "Describe this webpage in 3-5 sentences. Include: what it is, main purpose, visual style, one standout element.",
    "custom": "{custom_prompt}",
}


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class VisionResult:
    url: str = ""
    task: str = ""
    analysis: str = ""
    model_used: str = ""
    provider: str = ""
    elapsed_ms: int = 0
    error: Optional[str] = None


# ── Model Registry ────────────────────────────────────────────────────────────

class ModelRegistry:
    """
    Persistent vision model registry.
    Custom models survive restarts via data/vision_models.json.
    """

    def __init__(self, registry_path: str = "data/vision_models.json"):
        self.path = Path(registry_path)
        self._custom: list[dict] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._custom = json.loads(self.path.read_text()).get("custom", [])
            except Exception:
                self._custom = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"custom": self._custom}, indent=2))

    def all_openrouter(self) -> list[dict]:
        known = {m["id"] for m in OPENROUTER_FREE_VISION}
        custom_or = [m for m in self._custom
                     if m.get("provider") == "openrouter" and m["id"] not in known]
        return OPENROUTER_FREE_VISION + custom_or

    def all_ollama(self) -> list[dict]:
        known = {m["id"] for m in OLLAMA_VISION_MODELS}
        custom_ol = [m for m in self._custom
                     if m.get("provider") == "ollama" and m["id"] not in known]
        return OLLAMA_VISION_MODELS + custom_ol

    def all_hf(self) -> list[dict]:
        known = {m["id"] for m in HF_VISION_MODELS}
        custom_hf = [m for m in self._custom
                     if m.get("provider") == "huggingface" and m["id"] not in known]
        return HF_VISION_MODELS + custom_hf

    def all_custom_endpoints(self) -> list[dict]:
        return [m for m in self._custom if m.get("provider") == "custom_endpoint"]

    def add(self, model: dict) -> bool:
        if any(m["id"] == model["id"] for m in self._custom):
            return False
        self._custom.append(model)
        self._save()
        return True

    def remove(self, model_id: str) -> bool:
        before = len(self._custom)
        self._custom = [m for m in self._custom if m["id"] != model_id]
        if len(self._custom) < before:
            self._save()
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "openrouter_free": self.all_openrouter(),
            "ollama": self.all_ollama(),
            "huggingface": self.all_hf(),
            "custom_endpoints": self.all_custom_endpoints(),
            "total": (len(self.all_openrouter()) + len(self.all_ollama())
                      + len(self.all_hf()) + len(self.all_custom_endpoints())),
        }

    async def fetch_live_or_vision_models(self, api_key: str) -> list[dict]:
        """
        Auto-fetch vision-capable models from OpenRouter API.
        Call at startup or on demand via GET /models/vision/refresh.
        Returns list of newly discovered models (not already in registry).
        """
        if not api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
                raw = r.json().get("data", [])
        except Exception:
            return []

        known = {m["id"] for m in self.all_openrouter()}
        found = []
        for m in raw:
            arch = m.get("architecture", {})
            modality = str(arch.get("modality", "") or arch.get("input_modalities", ""))
            supports_img = (
                "image" in modality.lower()
                or "vl" in m["id"].lower()
                or "vision" in m["id"].lower()
                or "visual" in m["id"].lower()
            )
            price = float(m.get("pricing", {}).get("completion", "1") or 1)
            is_free = price == 0

            if supports_img and is_free and m["id"] not in known:
                entry = {
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "provider": "openrouter",
                    "free": True,
                    "context": m.get("context_length", 0),
                    "notes": f"Auto-fetched. Context: {m.get('context_length',0)}",
                }
                found.append(entry)
                self.add(entry)

        return found[:20]


# ── Vision Service ────────────────────────────────────────────────────────────

class VisionService:
    """
    Unified vision LLM service.
    Auto-cascade: Ollama → OpenRouter → HuggingFace.
    """

    def __init__(self, settings: Settings, registry: ModelRegistry = None):
        self.cfg = settings
        self.registry = registry or ModelRegistry()

    async def analyze_screenshot(
        self,
        screenshot_b64: str,
        task: str = "business_intel",
        url: str = "",
        custom_prompt: str = "",
        force_provider: str = "auto",
        model_id: str = "",
    ) -> VisionResult:
        start = time.time()
        prompt = self._build_prompt(task, custom_prompt)

        if model_id:
            result = await self._route_by_model_id(screenshot_b64, prompt, model_id)
        elif force_provider == "ollama":
            result = await self._try_ollama(screenshot_b64, prompt)
        elif force_provider == "openrouter":
            result = await self._try_openrouter(screenshot_b64, prompt)
        elif force_provider == "huggingface":
            result = await self._try_huggingface(screenshot_b64, prompt)
        else:  # auto cascade
            result = await self._try_ollama(screenshot_b64, prompt)
            if result.error:
                result = await self._try_openrouter(screenshot_b64, prompt)
            if result.error:
                result = await self._try_huggingface(screenshot_b64, prompt)

        result.url = url
        result.task = task
        result.elapsed_ms = round((time.time() - start) * 1000)
        return result

    async def analyze_many(
        self,
        items: list[dict],
        task: str = "business_intel",
        max_concurrent: int = 3,
        model_id: str = "",
    ) -> list[VisionResult]:
        import asyncio
        sem = asyncio.Semaphore(max_concurrent)

        async def bounded(item: dict) -> VisionResult:
            async with sem:
                return await self.analyze_screenshot(
                    screenshot_b64=item["screenshot_b64"],
                    task=task, url=item.get("url", ""), model_id=model_id,
                )

        results = await asyncio.gather(*[bounded(i) for i in items], return_exceptions=True)
        return [
            r if isinstance(r, VisionResult)
            else VisionResult(url=items[i].get("url", ""), error=str(r))
            for i, r in enumerate(results)
        ]

    # ── Backends ──────────────────────────────────────────────────────────────

    async def _try_ollama(self, b64: str, prompt: str, model: str = "") -> VisionResult:
        models = [model] if model else [m["id"] for m in self.registry.all_ollama()]
        for m in models[:4]:
            try:
                async with httpx.AsyncClient(timeout=120) as c:
                    r = await c.post(
                        f"{self.cfg.ollama_host}/api/chat",
                        json={"model": m, "stream": False,
                              "messages": [{"role": "user", "content": prompt, "images": [b64]}]},
                    )
                    if r.status_code == 200:
                        return VisionResult(
                            analysis=r.json()["message"]["content"],
                            model_used=f"ollama/{m}", provider="ollama",
                        )
            except Exception:
                continue
        return VisionResult(error="No Ollama vision model available", provider="ollama")

    async def _try_openrouter(self, b64: str, prompt: str, model: str = "") -> VisionResult:
        if not self.cfg.openrouter_api_key:
            return VisionResult(error="OPENROUTER_API_KEY not set", provider="openrouter")
        models = [model] if model else [m["id"] for m in self.registry.all_openrouter()]
        for m in models[:5]:
            try:
                async with httpx.AsyncClient(timeout=60) as c:
                    r = await c.post(
                        f"{self.cfg.openrouter_base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.cfg.openrouter_api_key}",
                                 "HTTP-Referer": self.cfg.openrouter_site_url,
                                 "X-Title": self.cfg.openrouter_app_name},
                        json={"model": m, "max_tokens": self.cfg.llm_max_tokens,
                              "messages": [{"role": "user", "content": [
                                  {"type": "image_url",
                                   "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                  {"type": "text", "text": prompt},
                              ]}]},
                    )
                    if r.status_code == 200:
                        return VisionResult(
                            analysis=r.json()["choices"][0]["message"]["content"],
                            model_used=f"openrouter/{m}", provider="openrouter",
                        )
            except Exception:
                continue
        return VisionResult(error="All OR vision models failed", provider="openrouter")

    async def _try_huggingface(self, b64: str, prompt: str, model: str = "") -> VisionResult:
        hf_token = getattr(self.cfg, "hf_token", "") or ""
        if not hf_token:
            return VisionResult(error="HF_TOKEN not set", provider="huggingface")
        models = [model] if model else [m["hf_id"] for m in self.registry.all_hf()
                                        if "hf_id" in m]
        for m in models[:3]:
            try:
                async with httpx.AsyncClient(timeout=60) as c:
                    r = await c.post(
                        "https://router.huggingface.co/v1/chat/completions",
                        headers={"Authorization": f"Bearer {hf_token}"},
                        json={"model": m, "max_tokens": self.cfg.llm_max_tokens,
                              "messages": [{"role": "user", "content": [
                                  {"type": "image_url",
                                   "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                  {"type": "text", "text": prompt},
                              ]}]},
                    )
                    if r.status_code == 200:
                        return VisionResult(
                            analysis=r.json()["choices"][0]["message"]["content"],
                            model_used=f"huggingface/{m}", provider="huggingface",
                        )
            except Exception:
                continue
        return VisionResult(error="HF Inference Providers failed", provider="huggingface")

    async def _route_by_model_id(self, b64: str, prompt: str, model_id: str) -> VisionResult:
        for ep in self.registry.all_custom_endpoints():
            if model_id in ep.get("models", []):
                try:
                    async with httpx.AsyncClient(timeout=90) as c:
                        r = await c.post(
                            f"{ep['base_url']}/chat/completions",
                            headers={"Authorization": f"Bearer {ep['api_key']}"},
                            json={"model": model_id, "messages": [{"role": "user", "content": [
                                {"type": "image_url",
                                 "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                {"type": "text", "text": prompt},
                            ]}]},
                        )
                        if r.status_code == 200:
                            return VisionResult(
                                analysis=r.json()["choices"][0]["message"]["content"],
                                model_used=f"custom/{model_id}", provider="custom",
                            )
                except Exception as e:
                    return VisionResult(error=str(e), provider="custom")

        # Detect provider from model_id format
        if model_id.startswith("ollama/"):
            return await self._try_ollama(b64, prompt, model_id[7:])
        elif "/" in model_id and not model_id.endswith(":free"):
            # Looks like HF model ID (org/model)
            if getattr(self.cfg, "hf_token", ""):
                return await self._try_huggingface(b64, prompt, model_id)
        return await self._try_openrouter(b64, prompt, model_id)

    def _build_prompt(self, task: str, custom_prompt: str = "") -> str:
        t = VISION_TASKS.get(task, VISION_TASKS["summary"])
        if task == "custom" or "{custom_prompt}" in t:
            return custom_prompt or "Describe this webpage."
        return t

    def list_models(self) -> dict:
        return self.registry.to_dict()


# ── Full visual audit ─────────────────────────────────────────────────────────

class VisualAuditPipeline:
    def __init__(self, settings: Settings, vision: VisionService, screenshots):
        self.cfg = settings
        self.vision = vision
        self.screenshots = screenshots

    async def run(
        self,
        url: str,
        max_pages: int = 10,
        tasks: list[str] = None,
        output_dir: str = "data/screenshots",
        model_id: str = "",
    ) -> dict:
        from src.sitemap import SiteMapService
        tasks = tasks or ["business_intel", "design_audit"]

        sitemap = SiteMapService(self.cfg)
        site = await sitemap.discover(url)
        pages = [url] + site.key_pages[:max_pages - 1]

        screenshots = await self.screenshots.capture_many(
            pages, max_concurrent=3, output_dir=output_dir,
        )
        valid = [{"url": s.url, "screenshot_b64": s.screenshot_b64}
                 for s in screenshots if s.screenshot_b64 and not s.error]

        insights: dict = {}
        for task in tasks:
            results = await self.vision.analyze_many(valid, task=task, model_id=model_id)
            insights[task] = [
                {"url": r.url, "analysis": r.analysis, "model": r.model_used}
                for r in results if not r.error
            ]

        return {
            "url": url,
            "pages_analyzed": [s.url for s in screenshots if not s.error],
            "screenshots_taken": len(valid),
            "sitemap_url_count": len(site.sitemap_urls),
            "key_pages_found": site.key_pages,
            "key_insights": insights,
        }
