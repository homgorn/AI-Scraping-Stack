"""
src/models.py — All Pydantic schemas
=====================================
Never define Pydantic models outside this file.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Scrape ──────────────────────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    url: str
    strategy: Literal["free", "fast", "smart", "llm", "ai", "premium", "stealth"] = (
        "smart"
    )
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    css_selector: str = ""
    mode: Literal["fast", "stealth", "dynamic"] = "fast"
    prompt: str = ""


class ScrapeResponse(BaseModel):
    url: str
    markdown: str = ""
    text: str = ""
    html: str = ""
    title: str = ""
    links: list[str] = []
    elements: list[str] = []
    provider: str = "unknown"
    analysis: str = ""
    model_used: str = ""
    cost_usd: float = 0.0
    elapsed_ms: int = 0
    error: Optional[str] = None


class BulkScrapeRequest(BaseModel):
    urls: list[str]
    strategy: str = "smart"
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    max_concurrent: int = 5


# ── Analyze ─────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    text: str
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    model_source: Literal["auto", "ollama", "openrouter"] = "auto"
    model_override: str = ""


class AnalyzeResponse(BaseModel):
    analysis: str
    model_used: str
    elapsed_ms: int
    cost_usd: float = 0.0
    error: Optional[str] = None


# ── Synthesis ───────────────────────────────────────────────────────────────


class SynthesizeRequest(BaseModel):
    urls: list[str]
    prompt: str
    output_format: Literal["html", "react", "fullstack_spec"] = "html"
    research_trends: bool = True
    complexity: Literal["low", "medium", "high"] = "high"


class SynthesizeMultiRequest(BaseModel):
    urls: list[str]
    prompt: str
    num_variants: int = 2


class SynthesizeResponse(BaseModel):
    prompt: str
    urls_processed: int
    code: str = ""
    html: str = ""
    spec: str = ""
    stack: str = ""
    insights: list[str] = []
    trends: list[str] = []
    elapsed_ms: int = 0
    cost_usd: float = 0.0
    error: str = ""


# ── Screenshot ──────────────────────────────────────────────────────────────


class ScreenshotRequest(BaseModel):
    url: str
    width: int = 1440
    height: int = 900
    full_page: bool = True
    save: bool = False
    pdf: bool = False
    wait_for: str = ""


class ScreenshotBulkRequest(BaseModel):
    urls: list[str]
    width: int = 1440
    full_page: bool = True
    max_concurrent: int = 3
    save: bool = True
    tasks: list[str] = ["business_intel"]


class SiteAuditRequest(BaseModel):
    url: str
    max_pages: int = 10
    tasks: list[str] = ["business_intel", "design_audit"]
    save_screenshots: bool = True


# ── Vision ──────────────────────────────────────────────────────────────────


class VisionAnalyzeRequest(BaseModel):
    screenshot_b64: str
    url: str = ""
    task: str = "business_intel"
    custom_prompt: str = ""
    force_cloud: bool = False


class VisionAnalyzeResponse(BaseModel):
    url: str
    task: str
    analysis: str
    model_used: str
    elapsed_ms: int
    error: Optional[str] = None


# ── Models management ───────────────────────────────────────────────────────


class OllamaPullRequest(BaseModel):
    model_name: str


class OpenRouterModelRequest(BaseModel):
    model_id: str
    name: str
    free: bool = False
    tier: Literal["low", "medium", "high"] = "medium"


class CustomApiRequest(BaseModel):
    name: str
    base_url: str
    api_key: str
    models: list[str]
    description: str = ""


# ── History / Stats ─────────────────────────────────────────────────────────


class HistoryEntry(BaseModel):
    id: int
    url: str
    provider: str
    task: str
    model_used: str
    cost_usd: float
    elapsed_ms: int
    timestamp: str
    error: Optional[str] = None


class StatsResponse(BaseModel):
    total_scrapes: int = 0
    total_cost_usd: float = 0.0
    avg_elapsed_ms: float = 0.0
    top_providers: dict = {}
    top_models: dict = {}
    success_rate: float = 0.0
