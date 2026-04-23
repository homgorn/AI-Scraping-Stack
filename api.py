"""
FastAPI Backend — AI Scraping Stack (Unified)
=============================================
Run: uvicorn api:app --reload --port 8100

All routes:
  GET  /                          → health
  GET  /status                    → service status
  GET  /config                    → current config (keys masked)
  PATCH /config                   → update config
  POST /scrape                    → single URL + LLM analysis
  POST /scrape/bulk               → N URLs parallel
  POST /analyze                   → raw text → LLM
  POST /synthesize                → N URLs → website code
  POST /synthesize/multi          → N URLs → multiple variants
  POST /screenshot                → capture screenshot
  POST /screenshot/bulk           → N screenshots + VLM
  POST /screenshot/audit          → full visual audit
  POST /vision/analyze            → analyze screenshot with VLM
  GET  /sitemap                   → discover site structure
  GET  /vision/models             → list VLM models
  GET  /models                    → all models (Ollama + OR + custom)
  POST /models/ollama/pull        → pull model (SSE)
  DELETE /models/ollama/{name}
  POST /models/openrouter
  DELETE /models/openrouter/{id}
  POST /models/api
  DELETE /models/api/{name}
  GET  /models/openrouter/search
  GET  /history                   → scrape history
  GET  /stats                     → aggregate stats
"""

import asyncio
import json
import logging
import os
import secrets
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Security Config ───────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
_rate_limit_store: dict[str, list[float]] = {}


async def security_middleware(request: Request, call_next):
    """Rate limiting + API Key protection."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < 60]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(429, "Too many requests. Please wait a moment.")
    _rate_limit_store[client_ip].append(now)

    if API_KEY:
        auth = request.headers.get("X-API-Key", "")
        if not secrets.compare_digest(auth, API_KEY):
            logger.warning(f"Invalid API key attempt from IP: {client_ip}")
            raise HTTPException(403, "Forbidden: Invalid API Key")

    return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # 1. Rate Limiting
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    # Remove old entries
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if now - t < 60]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT:
        raise HTTPException(429, "Too many requests. Please wait a moment.")
    _rate_limit_store[client_ip].append(now)

    # 2. API Key Check (only if API_KEY env var is set)
    if API_KEY:
        auth = request.headers.get("X-API-Key", "")
        if auth != API_KEY:
            raise HTTPException(403, "Forbidden: Invalid API Key")

    return await call_next(request)


from src.config import get_settings
from src.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    BulkScrapeRequest,
    ScrapeRequest,
    ScrapeResponse,
    SynthesizeMultiRequest,
    SynthesizeRequest,
    SynthesizeResponse,
    ScreenshotRequest,
    ScreenshotBulkRequest,
    SiteAuditRequest,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    OllamaPullRequest,
    OpenRouterModelRequest,
    CustomApiRequest,
    HistoryEntry,
    StatsResponse,
)
from src.scraper import ScraperService
from src.llm import LLMRouter
from src.storage import Storage

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="AI Scraping Stack API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(security_middleware)

# ── Service factories (lazy init) ─────────────────────────────────────────────


def _scraper():
    return ScraperService(get_settings())


def _llm():
    return LLMRouter(get_settings())


def _storage():
    s = Storage(get_settings())
    return s


# ── OpenRouter builtin models ─────────────────────────────────────────────────

OPENROUTER_BUILTIN_MODELS = [
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "free": False,
        "tier": "high",
    },
    {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "free": False,
        "tier": "medium",
    },
    {"id": "openai/gpt-4o", "name": "GPT-4o", "free": False, "tier": "high"},
    {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini",
        "free": False,
        "tier": "medium",
    },
    {
        "id": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash",
        "free": True,
        "tier": "medium",
    },
    {
        "id": "google/gemma-3-27b-it:free",
        "name": "Gemma 3 27B",
        "free": True,
        "tier": "medium",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B",
        "free": True,
        "tier": "high",
    },
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Llama 3.2 3B",
        "free": True,
        "tier": "low",
    },
    {
        "id": "qwen/qwen3-30b-a3b:free",
        "name": "Qwen3 30B",
        "free": True,
        "tier": "medium",
    },
    {
        "id": "mistralai/mistral-nemo:free",
        "name": "Mistral Nemo",
        "free": True,
        "tier": "medium",
    },
    {
        "id": "deepseek/deepseek-r1:free",
        "name": "DeepSeek R1",
        "free": True,
        "tier": "high",
    },
    {
        "id": "microsoft/phi-3-mini-128k-instruct:free",
        "name": "Phi-3 Mini",
        "free": True,
        "tier": "low",
    },
]

# ── Config models (runtime, persisted to storage) ─────────────────────────────


class ConfigUpdate(BaseModel):
    openrouter_api_key: Optional[str] = None
    ollama_host: Optional[str] = None
    default_ollama_model: Optional[str] = None
    default_openrouter_model: Optional[str] = None
    proxy: Optional[str] = None
    max_concurrent: Optional[int] = None
    default_fetch_mode: Optional[str] = None


class AddOllamaModel(BaseModel):
    model_name: str


class AddOpenRouterModel(BaseModel):
    model_id: str
    name: str
    free: bool = False
    tier: Literal["low", "medium", "high"] = "medium"


class AddCustomAPI(BaseModel):
    name: str
    base_url: str
    api_key: str
    models: list[str]
    description: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _ollama_models() -> list[dict]:
    cfg = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{cfg.ollama_host}/api/tags")
            if r.status_code == 200:
                return [
                    {
                        "id": m["name"],
                        "name": m["name"],
                        "size": round(m.get("size", 0) / 1e9, 1),
                        "installed": True,
                    }
                    for m in r.json().get("models", [])
                ]
    except Exception as e:
        logger.warning(f"Failed to fetch Ollama models: {e}")
    return []


def _load_registry() -> dict:
    return _storage().load_model_registry()


def _save_registry(data: dict):
    _storage().save_model_registry(data)


# ── Core routes ───────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return {"status": "ok", "version": "1.0.0", "docs": "/docs"}


@app.get("/status")
async def status():
    cfg = get_settings()
    models = await _ollama_models()
    scrapling_ok = False
    scrapling_ver = "not installed"
    try:
        import scrapling

        scrapling_ok = True
        scrapling_ver = getattr(scrapling, "__version__", "installed")
    except ImportError:
        pass
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{cfg.ollama_host}/api/tags")
            ollama_online = r.status_code == 200
    except Exception:
        pass

    reg = _load_registry()
    return {
        "timestamp": datetime.now().isoformat(),
        "ollama": {
            "online": ollama_online,
            "models_count": len(models),
            "host": cfg.ollama_host,
        },
        "openrouter": {"configured": bool(cfg.openrouter_api_key)},
        "scrapling": {"installed": scrapling_ok, "version": scrapling_ver},
        "custom_apis": len(reg.get("custom_apis", [])),
        "custom_models": len(reg.get("openrouter_models", [])),
    }


@app.get("/config")
async def get_config():
    cfg = get_settings()
    reg = _load_registry()
    overrides = reg.get("config_overrides", {})
    result = {
        "ollama_host": overrides.get("ollama_host", cfg.ollama_host),
        "default_ollama_model": overrides.get("default_ollama_model", cfg.ollama_model),
        "default_openrouter_model": overrides.get("default_openrouter_model", cfg.openrouter_model),
        "proxy": overrides.get("proxy", cfg.proxy_url),
        "max_concurrent": overrides.get("max_concurrent", cfg.max_concurrent),
        "default_fetch_mode": overrides.get("default_fetch_mode", cfg.default_fetch_mode),
    }
    if cfg.openrouter_api_key:
        result["openrouter_api_key"] = cfg.openrouter_api_key[:8] + "..." + cfg.openrouter_api_key[-4:]
    return result


@app.patch("/config")
async def update_config(update: ConfigUpdate):
    reg = _load_registry()
    if "config_overrides" not in reg:
        reg["config_overrides"] = {}
    for field, val in update.model_dump(exclude_none=True).items():
        reg["config_overrides"][field] = val
    _save_registry(reg)
    get_settings.cache_clear()
    return {"ok": True}


# ── Scrape routes ─────────────────────────────────────────────────────────────


@app.post("/scrape")
async def scrape_single(req: ScrapeRequest):
    svc = _scraper()
    result = await svc.scrape(req)
    try:
        storage = _storage()
        await storage.init()
        await storage.save_result(result, task=req.task)
    except Exception as e:
        logger.error(f"Failed to save scrape result to history: {e}")
    return result.model_dump()


@app.post("/scrape/bulk")
async def scrape_bulk(req: BulkScrapeRequest):
    svc = _scraper()
    results = await svc.scrape_bulk(
        urls=req.urls,
        strategy=req.strategy,
        task=req.task,
        complexity=req.complexity,
        max_concurrent=req.max_concurrent,
    )
    return {
        "results": [r.model_dump() for r in results],
        "total": len(req.urls),
        "success": sum(1 for r in results if not r.error),
    }


@app.post("/analyze")
async def analyze_text(req: AnalyzeRequest):
    llm = _llm()
    result = await llm.analyze(
        text=req.text,
        task=req.task,
        complexity=req.complexity,
        model_source=req.model_source,
        model_override=req.model_override,
    )
    return result.model_dump()


# ── Synthesis routes ──────────────────────────────────────────────────────────


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    from src.synthesizer import WebSynthesizer

    cfg = get_settings()
    llm = _llm()
    synth = WebSynthesizer(cfg, llm)
    result = await synth.run(
        urls=req.urls,
        prompt=req.prompt,
        output_format=req.output_format,
        research_trends=req.research_trends,
        complexity=req.complexity,
    )
    return {
        "prompt": result.prompt,
        "urls_processed": result.urls_processed,
        "code": result.code,
        "html": result.html,
        "spec": result.spec,
        "stack": result.stack,
        "insights": result.insights,
        "trends": result.trends,
        "elapsed_ms": result.elapsed_ms,
        "cost_usd": result.cost_usd,
        "error": result.error,
    }


@app.post("/synthesize/multi")
async def synthesize_multi(req: SynthesizeMultiRequest):
    from src.synthesizer import WebSynthesizer

    cfg = get_settings()
    llm = _llm()
    synth = WebSynthesizer(cfg, llm)
    results = await synth.run_multi_output(
        urls=req.urls,
        prompt=req.prompt,
        num_variants=req.num_variants,
    )
    return [
        {
            "prompt": r.prompt,
            "urls_processed": r.urls_processed,
            "code": r.code,
            "html": r.html,
            "spec": r.spec,
            "stack": r.stack,
            "insights": r.insights,
            "trends": r.trends,
            "elapsed_ms": r.elapsed_ms,
            "cost_usd": r.cost_usd,
            "error": r.error,
        }
        for r in results
    ]


# ── Screenshot routes ─────────────────────────────────────────────────────────


@app.post("/screenshot")
async def capture_screenshot(req: ScreenshotRequest):
    from src.screenshot import ScreenshotService

    svc = ScreenshotService(get_settings())
    result = await svc.capture(
        url=req.url,
        width=req.width,
        height=req.height,
        full_page=req.full_page,
        output_dir="data/screenshots" if req.save else "",
        pdf=req.pdf,
        wait_for=req.wait_for,
    )
    if result.error:
        raise HTTPException(500, f"Screenshot failed: {result.error}")
    return {
        "url": result.url,
        "screenshot_b64": result.screenshot_b64,
        "screenshot_path": result.screenshot_path,
        "pdf_b64": result.pdf_b64 if req.pdf else "",
        "provider": result.provider,
        "width": result.width,
        "height": result.height,
        "elapsed_ms": result.elapsed_ms,
    }


@app.post("/screenshot/bulk")
async def capture_screenshots_bulk(req: ScreenshotBulkRequest):
    if len(req.urls) > 50:
        raise HTTPException(400, "Max 50 URLs per bulk request")
    from src.screenshot import ScreenshotService
    from src.vision import VisionService

    svc = ScreenshotService(get_settings())
    vision = VisionService(get_settings())
    screenshots = await svc.capture_many(
        urls=req.urls,
        max_concurrent=req.max_concurrent,
        output_dir="data/screenshots" if req.save else "",
        width=req.width,
        full_page=req.full_page,
    )
    results = []
    for s in screenshots:
        item = {
            "url": s.url,
            "provider": s.provider,
            "elapsed_ms": s.elapsed_ms,
            "error": s.error,
            "has_screenshot": bool(s.screenshot_b64),
            "screenshot_path": s.screenshot_path,
        }
        if s.screenshot_b64 and not s.error and req.tasks:
            analyses = {}
            for task in req.tasks[:3]:
                vr = await vision.analyze_screenshot(s.screenshot_b64, task=task, url=s.url)
                analyses[task] = vr.analysis if not vr.error else f"Error: {vr.error}"
                analyses[f"{task}_model"] = vr.model_used
            item["analyses"] = analyses
        results.append(item)
    return {
        "results": results,
        "total": len(req.urls),
        "success": sum(1 for r in results if r.get("has_screenshot")),
    }


@app.post("/screenshot/audit")
async def visual_audit(req: SiteAuditRequest):
    from src.vision import VisualAuditPipeline
    from src.screenshot import ScreenshotService
    from src.vision import VisionService

    svc = ScreenshotService(get_settings())
    vision = VisionService(get_settings())
    pipeline = VisualAuditPipeline(
        settings=get_settings(),
        vision=vision,
        screenshots=svc,
    )
    audit = await pipeline.run(
        url=req.url,
        max_pages=min(req.max_pages, 15),
        tasks=req.tasks,
        output_dir="data/screenshots" if req.save_screenshots else "",
    )
    return audit


# ── Vision routes ─────────────────────────────────────────────────────────────


@app.post("/vision/analyze")
async def analyze_vision(req: VisionAnalyzeRequest):
    from src.vision import VisionService

    vision = VisionService(get_settings())
    result = await vision.analyze_screenshot(
        screenshot_b64=req.screenshot_b64,
        task=req.task,
        url=req.url,
        custom_prompt=req.custom_prompt,
        force_cloud=req.force_cloud,
    )
    if result.error:
        raise HTTPException(500, f"Vision analysis failed: {result.error}")
    return {
        "url": result.url,
        "task": result.task,
        "analysis": result.analysis,
        "model_used": result.model_used,
        "elapsed_ms": result.elapsed_ms,
    }


@app.get("/sitemap")
async def discover_sitemap(url: str, max_urls: int = 200):
    from src.sitemap import SiteMapService

    svc = SiteMapService(get_settings())
    result = await svc.discover(url, max_sitemap_urls=max_urls)
    return {
        "url": result.url,
        "sitemap_url_count": len(result.sitemap_urls),
        "key_pages": result.key_pages,
        "sitemap_urls": result.sitemap_urls[:50],
        "disallowed": result.disallowed,
        "robots_txt_present": bool(result.robots_txt),
    }


@app.get("/vision/models")
async def list_vision_models():
    from src.vision import VisionService

    vision = VisionService(get_settings())
    return vision.list_available_models()


# ── Model management routes ───────────────────────────────────────────────────


@app.get("/models")
async def list_models():
    ollama_models = await _ollama_models()
    reg = _load_registry()
    return {
        "ollama": ollama_models,
        "openrouter": OPENROUTER_BUILTIN_MODELS + reg.get("openrouter_models", []),
        "custom_apis": [
            {"name": a["name"], "base_url": a["base_url"], "models": a["models"]} for a in reg.get("custom_apis", [])
        ],
        "defaults": {
            "ollama": get_settings().ollama_model,
            "openrouter": get_settings().openrouter_model,
        },
    }


@app.post("/models/ollama/pull")
async def pull_ollama_model(body: OllamaPullRequest):
    async def do_pull() -> AsyncGenerator[str, None]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "pull",
                body.model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            async for line in proc.stdout:
                yield f"data: {line.decode().strip()}\n\n"
            await proc.wait()
            yield f"data: DONE:{body.model_name}\n\n"
        except FileNotFoundError:
            yield "data: ERROR:ollama not found in PATH\n\n"
        except Exception as e:
            yield f"data: ERROR:{e}\n\n"

    return StreamingResponse(do_pull(), media_type="text/event-stream")


@app.delete("/models/ollama/{model_name}")
async def delete_ollama_model(model_name: str):
    cfg = get_settings()
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.delete(f"{cfg.ollama_host}/api/delete", json={"name": model_name})
            r.raise_for_status()
        return {"ok": True, "deleted": model_name}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/models/openrouter")
async def add_openrouter_model(body: OpenRouterModelRequest):
    reg = _load_registry()
    existing = [m.get("model_id") for m in reg.get("openrouter_models", [])]
    if body.model_id in existing:
        raise HTTPException(409, "Already added")
    reg.setdefault("openrouter_models", []).append(body.model_dump())
    _save_registry(reg)
    return {"ok": True}


@app.delete("/models/openrouter/{model_id:path}")
async def remove_openrouter_model(model_id: str):
    reg = _load_registry()
    reg["openrouter_models"] = [m for m in reg.get("openrouter_models", []) if m.get("model_id") != model_id]
    _save_registry(reg)
    return {"ok": True}


@app.post("/models/api")
async def add_custom_api(body: CustomApiRequest):
    reg = _load_registry()
    reg.setdefault("custom_apis", []).append(body.model_dump())
    _save_registry(reg)
    return {"ok": True}


@app.delete("/models/api/{api_name}")
async def remove_custom_api(api_name: str):
    reg = _load_registry()
    reg["custom_apis"] = [a for a in reg.get("custom_apis", []) if a.get("name") != api_name]
    _save_registry(reg)
    return {"ok": True}


@app.get("/models/openrouter/search")
async def search_openrouter_models(q: str = "", free_only: bool = False):
    models = OPENROUTER_BUILTIN_MODELS
    if q:
        models = [m for m in models if q.lower() in m["id"].lower() or q.lower() in m["name"].lower()]
    if free_only:
        models = [m for m in models if m["free"]]
    return {"models": models}


# ── History & Stats ───────────────────────────────────────────────────────────


@app.get("/history")
async def get_history(limit: int = 50, offset: int = 0, url: str = ""):
    # Enforce pagination limits
    limit = min(limit, 200)  # Max 200 per request
    offset = max(offset, 0)
    storage = _storage()
    await storage.init()
    entries = await storage.get_history(limit=limit, offset=offset, url_filter=url)
    return {
        "entries": [e.model_dump() for e in entries],
        "total": len(entries),
        "limit": limit,
        "offset": offset,
        "has_more": len(entries) == limit,
    }


@app.get("/stats")
async def get_stats():
    storage = _storage()
    await storage.init()
    stats = await storage.get_stats()
    return stats.model_dump()


# ── Run ───────────────────────────────────────────────────────────────────────


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown: close DB connections, clean up resources."""
    import logging

    logging.info("Shutting down AI Scraping Stack...")
    # Clear rate limit store
    _rate_limit_store.clear()
    # Clear settings cache
    get_settings.cache_clear()
    logging.info("Shutdown complete.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
        log_level="info",
        access_log=True,
    )
