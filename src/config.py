"""
src/config.py — Centralized Pydantic Settings
==============================================
All environment variables live here. Never use os.getenv() outside this file.
Access via get_settings() which is cached.

Usage:
    from src.config import get_settings
    cfg = get_settings()
    print(cfg.ollama_host)
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Core ──────────────────────────────────────────────────────────────
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")

    # ── OpenRouter ────────────────────────────────────────────────────────
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet", alias="OPENROUTER_MODEL"
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://github.com/ai-scraping-stack"
    openrouter_app_name: str = "AI Scraping Stack"

    # ── Free providers ────────────────────────────────────────────────────
    jina_api_key: str = Field(default="", alias="JINA_API_KEY")
    firecrawl_api_key: str = Field(default="", alias="FIRECRAWL_API_KEY")

    # ── Paid providers ────────────────────────────────────────────────────
    scrapingdog_key: str = Field(default="", alias="SCRAPINGDOG_KEY")
    scraperapi_key: str = Field(default="", alias="SCRAPERAPI_KEY")
    zenrows_key: str = Field(default="", alias="ZENROWS_KEY")
    scrapingbee_key: str = Field(default="", alias="SCRAPINGBEE_KEY")
    scrapedo_key: str = Field(default="", alias="SCRAPEDO_KEY")

    # ── Enterprise (optional) ─────────────────────────────────────────────
    brightdata_key: str = Field(default="", alias="BRIGHTDATA_KEY")
    zyte_api_key: str = Field(default="", alias="ZYTE_API_KEY")

    # ── Custom LLM APIs ───────────────────────────────────────────────────
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    together_api_key: str = Field(default="", alias="TOGETHER_API_KEY")
    perplexity_api_key: str = Field(default="", alias="PERPLEXITY_API_KEY")
    deepinfra_api_key: str = Field(default="", alias="DEEPINFRA_API_KEY")
    fireworks_api_key: str = Field(default="", alias="FIREWORKS_API_KEY")

    # ── Proxy ─────────────────────────────────────────────────────────────
    proxy_url: str = Field(default="", alias="PROXY_URL")

    # ── LLM ───────────────────────────────────────────────────────────────
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # ── Server ────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8100
    max_concurrent: int = 5

    # ── Storage ───────────────────────────────────────────────────────────
    db_path: str = "data/scrapling.db"
    model_registry_path: str = "data/models.json"
    screenshots_dir: str = "data/screenshots"

    # ── Default fetch mode ────────────────────────────────────────────────
    default_fetch_mode: str = "fast"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings — call get_settings.cache_clear() to reload."""
    return Settings()
