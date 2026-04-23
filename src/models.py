"""
src/models.py — All Pydantic schemas
=====================================
Never define Pydantic models outside this file.
"""

import ipaddress
import re
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


VALID_TASKS = {"summarize", "extract_entities", "classify", "extract_prices",
               "sentiment", "extract_links", "translate_ru", "translate_en",
               "business_intel", "design_audit", "competitor_analysis", "tech_stack",
               "ux_patterns", "ocr_extract", "content_extract", "summary"}

BLOCKED_PROTOCOLS = {"file", "javascript", "data", "ftp", "sftp", "ssh"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def validate_url(value: str) -> str:
    """Validate URL and prevent SSRF attacks."""
    if not value:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(value)

    if not parsed.scheme:
        raise ValueError("URL must include scheme (http:// or https://)")

    if parsed.scheme.lower() in BLOCKED_PROTOCOLS:
        raise ValueError(f"Protocol '{parsed.scheme}' is not allowed")

    if not parsed.hostname:
        raise ValueError("URL must have valid hostname")

    hostname_lower = parsed.hostname.lower()

    if hostname_lower in BLOCKED_HOSTS:
        raise ValueError(f"Hostname '{hostname_lower}' is not allowed")

    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_reserved:
            raise ValueError(f"Private/reserved IP addresses are not allowed")
    except ValueError:
        pass

    return value


# ── Scrape ──────────────────────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=4096)
    strategy: Literal["free", "fast", "smart", "llm", "ai", "premium", "stealth"] = (
        "smart"
    )
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    css_selector: str = ""
    mode: Literal["fast", "stealth", "dynamic"] = "fast"
    prompt: str = ""

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, v: str) -> str:
        return validate_url(v)

    @field_validator("task")
    @classmethod
    def task_must_be_valid(cls, v: str) -> str:
        if v.startswith("qa:") or v.startswith("custom:"):
            return v
        if v not in VALID_TASKS:
            raise ValueError(f"Invalid task: {v}. Must be one of: {', '.join(sorted(VALID_TASKS))}")
        return v


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
    urls: list[str] = Field(..., min_length=1, max_length=100)
    strategy: str = "smart"
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    max_concurrent: int = 5

    @field_validator("urls")
    @classmethod
    def urls_must_be_valid(cls, v: list[str]) -> list[str]:
        for url in v:
            validate_url(url)
        return v


# ── Analyze ─────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    task: str = "summarize"
    complexity: Literal["low", "medium", "high"] = "low"
    model_source: Literal["auto", "ollama", "openrouter"] = "auto"
    model_override: str = ""

    @field_validator("task")
    @classmethod
    def task_must_be_valid(cls, v: str) -> str:
        if v.startswith("qa:") or v.startswith("custom:"):
            return v
        if v not in VALID_TASKS:
            raise ValueError(f"Invalid task: {v}. Must be one of: {', '.join(sorted(VALID_TASKS))}")
        return v


class AnalyzeResponse(BaseModel):
    analysis: str
    model_used: str
    elapsed_ms: int
    cost_usd: float = 0.0
    error: Optional[str] = None


# ── Synthesis ───────────────────────────────────────────────────────────────


class SynthesizeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=50)
    prompt: str = Field(..., min_length=1, max_length=10000)
    output_format: Literal["html", "react", "fullstack_spec"] = "html"
    research_trends: bool = True
    complexity: Literal["low", "medium", "high"] = "high"

    @field_validator("urls")
    @classmethod
    def urls_must_be_valid(cls, v: list[str]) -> list[str]:
        for url in v:
            validate_url(url)
        return v


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
    url: str = Field(..., min_length=1, max_length=4096)
    width: int = 1440
    height: int = 900
    full_page: bool = True
    save: bool = False
    pdf: bool = False
    wait_for: str = ""

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, v: str) -> str:
        return validate_url(v)


class ScreenshotBulkRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=50)
    width: int = 1440
    full_page: bool = True
    max_concurrent: int = 3
    save: bool = True
    tasks: list[str] = ["business_intel"]

    @field_validator("urls")
    @classmethod
    def urls_must_be_valid(cls, v: list[str]) -> list[str]:
        for url in v:
            validate_url(url)
        return v


class SiteAuditRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=4096)
    max_pages: int = 10
    tasks: list[str] = ["business_intel", "design_audit"]
    save_screenshots: bool = True

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, v: str) -> str:
        return validate_url(v)


# ── Vision ──────────────────────────────────────────────────────────────────


class VisionAnalyzeRequest(BaseModel):
    screenshot_b64: str = Field(..., min_length=1)
    url: str = ""
    task: str = "business_intel"
    custom_prompt: str = ""
    force_cloud: bool = False

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, v: str) -> str:
        if v:
            validate_url(v)
        return v


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
