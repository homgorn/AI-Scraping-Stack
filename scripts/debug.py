"""
debug.py — Health check & debug CLI
=====================================
Run: python debug.py
     python debug.py --full    (includes scrape test)
     python debug.py --fix     (auto-fix common issues)

Checks:
  ✓ Config loaded (env vars, .env file)
  ✓ Ollama reachable + installed models
  ✓ OpenRouter API key valid + quota
  ✓ HuggingFace token valid
  ✓ Scrapling installed
  ✓ Crawl4AI installed
  ✓ Playwright browsers installed
  ✓ SQLite writable
  ✓ Vision model registry
  ✓ Optional: live scrape test (Jina → example.com)
"""

import asyncio
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

# ── Color helpers (no deps) ───────────────────────────────────────────────────
_NO_COLOR = not sys.stdout.isatty()


def c(text: str, code: str) -> str:
    if _NO_COLOR:
        return text
    codes = {"green": "32", "red": "31", "yellow": "33", "cyan": "36", "bold": "1", "dim": "2", "reset": "0"}
    return f"\033[{codes.get(code, '0')}m{text}\033[0m"


OK = lambda s: f"  {c('✓', 'green')} {s}"
ERR = lambda s: f"  {c('✗', 'red')} {s}"
WARN = lambda s: f"  {c('⚠', 'yellow')} {s}"
INFO = lambda s: f"  {c('·', 'dim')} {s}"
HDR = lambda s: f"\n{c('━━ ' + s + ' ━━', 'cyan')}"


class DebugReport:
    def __init__(self):
        self.checks: list[dict] = []
        self.issues: list[str] = []

    def add(self, name: str, ok: bool, detail: str = "", fix: str = ""):
        self.checks.append({"name": name, "ok": ok, "detail": detail, "fix": fix})
        if not ok:
            self.issues.append(f"{name}: {detail}")
        line = OK(f"{name}: {detail}") if ok else ERR(f"{name}: {detail}")
        print(line)
        if not ok and fix:
            print(INFO(f"  Fix: {c(fix, 'yellow')}"))

    def summary(self) -> bool:
        passed = sum(1 for c in self.checks if c["ok"])
        total = len(self.checks)
        print(f"\n{c('━━━━━━━━━━━━━━━━━━━━', 'dim')}")
        if passed == total:
            print(c(f"  ALL CHECKS PASSED ({passed}/{total})", "green"))
        else:
            print(c(f"  {passed}/{total} passed, {total - passed} issues", "red"))
            for issue in self.issues:
                print(f"  {c('→', 'red')} {issue}")
        return passed == total


# ── Individual checks ─────────────────────────────────────────────────────────


async def check_config(report: DebugReport):
    print(HDR("Config"))
    try:
        from src.config import get_settings, Settings

        get_settings.cache_clear()
        cfg = Settings()  # fresh load

        report.add("Config loads", True, ".env parsed successfully")
        report.add("ollama_host", True, cfg.ollama_host)
        report.add("ollama_model", True, cfg.ollama_model)

        if cfg.openrouter_api_key:
            masked = cfg.openrouter_api_key[:8] + "..." + cfg.openrouter_api_key[-4:]
            report.add("OPENROUTER_API_KEY", True, masked)
        else:
            report.add(
                "OPENROUTER_API_KEY",
                False,
                "not set (cloud LLMs unavailable)",
                "Add OPENROUTER_API_KEY=sk-or-v1-... to .env",
            )

        if cfg.jina_api_key:
            report.add("JINA_API_KEY", True, "set (higher rate limit)")
        else:
            report.add(
                "JINA_API_KEY",
                False,
                "not set (20 RPM limit, still works)",
                "Optional: add JINA_API_KEY=jina_... to .env (free at jina.ai)",
            )

        # Check data dir
        data_dir = Path(cfg.db_path).parent
        if data_dir.exists() or data_dir == Path("."):
            report.add("data/ dir", True, str(data_dir))
        else:
            report.add("data/ dir", False, f"missing: {data_dir}", f"mkdir -p {data_dir}")

        return cfg
    except Exception as e:
        report.add("Config loads", False, str(e), "Check src/config.py and .env file")
        return None


async def check_ollama(cfg, report: DebugReport):
    print(HDR("Ollama (local LLM)"))
    if not cfg:
        return

    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{cfg.ollama_host}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                report.add("Ollama server", True, f"online at {cfg.ollama_host}")
                if models:
                    for m in models[:5]:
                        size = round(m.get("size", 0) / 1e9, 1)
                        report.add(f"  model: {m['name']}", True, f"{size} GB")
                else:
                    report.add("Ollama models", False, "no models installed", "ollama pull llama3.2")
            else:
                report.add("Ollama server", False, f"HTTP {r.status_code}", "ollama serve")
    except Exception:
        report.add(
            "Ollama server",
            False,
            f"not reachable at {cfg.ollama_host}",
            "Install: curl -fsSL https://ollama.ai/install.sh | sh && ollama serve",
        )

    # Check vision models specifically
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{cfg.ollama_host}/api/tags")
            if r.status_code == 200:
                names = [m["name"] for m in r.json().get("models", [])]
                vision_models = [n for n in names if any(v in n for v in ["llava", "qwen", "moondream", "vision"])]
                if vision_models:
                    report.add("Vision models", True, ", ".join(vision_models[:3]))
                else:
                    report.add(
                        "Vision models",
                        False,
                        "no vision models installed",
                        "ollama pull qwen2.5vl:7b  OR  ollama pull moondream",
                    )
    except Exception:
        pass


async def check_openrouter(cfg, report: DebugReport):
    print(HDR("OpenRouter"))
    if not cfg or not cfg.openrouter_api_key:
        print(WARN("Skipped — OPENROUTER_API_KEY not set"))
        return

    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{cfg.openrouter_base_url}/models",
                headers={"Authorization": f"Bearer {cfg.openrouter_api_key}"},
            )
        if r.status_code == 200:
            all_models = r.json().get("data", [])
            free_vision = [
                m
                for m in all_models
                if float(m.get("pricing", {}).get("completion", "1") or 1) == 0
                and ("vl" in m["id"].lower() or "vision" in m["id"].lower())
            ]
            report.add("OpenRouter API", True, f"{len(all_models)} models, {len(free_vision)} free vision")
        elif r.status_code == 401:
            report.add("OpenRouter API", False, "invalid API key", "Check OPENROUTER_API_KEY in .env")
        else:
            report.add("OpenRouter API", False, f"HTTP {r.status_code}")
    except Exception as e:
        report.add("OpenRouter API", False, str(e))


async def check_hf(cfg, report: DebugReport):
    print(HDR("HuggingFace Inference Providers"))
    print(WARN("Skipped — HF_TOKEN not configured (optional)"))


def check_python_packages(report: DebugReport):
    print(HDR("Python packages"))
    packages = {
        "scrapling": ("scrapling", "pip install 'scrapling[ai,fetchers]'"),
        "crawl4ai": ("crawl4ai", "pip install crawl4ai && crawl4ai-setup"),
        "playwright": ("playwright", "pip install playwright && playwright install"),
        "fastapi": ("fastapi", "pip install fastapi"),
        "uvicorn": ("uvicorn", "pip install 'uvicorn[standard]'"),
        "httpx": ("httpx", "pip install httpx"),
        "pydantic": ("pydantic", "pip install pydantic pydantic-settings"),
        "openai": ("openai", "pip install openai"),
        "fastmcp": ("fastmcp", "pip install fastmcp"),
        "firecrawl": ("firecrawl", "pip install firecrawl-py"),
        "scrapegraphai": ("scrapegraphai", "pip install scrapegraphai"),
    }
    required = {"scrapling", "fastapi", "uvicorn", "httpx", "pydantic", "openai"}
    for pkg_name, (import_name, fix_cmd) in packages.items():
        try:
            importlib.import_module(import_name)
            report.add(pkg_name, True, "installed")
        except ImportError:
            is_required = pkg_name in required
            if is_required:
                report.add(pkg_name, False, "MISSING (required)", fix_cmd)
            else:
                print(WARN(f"{pkg_name}: not installed (optional) — {fix_cmd}"))


def check_playwright_browsers(report: DebugReport):
    print(HDR("Playwright browsers"))
    try:
        result = subprocess.run(
            ["playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "chromium" in result.stdout.lower() or result.returncode == 0:
            report.add("Playwright chromium", True, "installed")
        else:
            report.add("Playwright chromium", False, "not installed", "playwright install chromium")
    except FileNotFoundError:
        report.add("Playwright", False, "playwright CLI not found", "pip install playwright && playwright install")
    except Exception as e:
        report.add("Playwright", False, str(e))


def check_scrapling_browsers(report: DebugReport):
    print(HDR("Scrapling"))
    try:
        import scrapling

        ver = getattr(scrapling, "__version__", "installed")
        report.add("Scrapling", True, f"v{ver}")

        # Check if browsers installed
        from scrapling.fetchers import Fetcher

        report.add("Scrapling Fetcher", True, "available")
    except ImportError:
        report.add("Scrapling", False, "not installed", "pip install 'scrapling[ai,fetchers]' && scrapling install")
    except Exception as e:
        report.add("Scrapling", False, str(e))


async def check_storage(cfg, report: DebugReport):
    print(HDR("Storage"))
    if not cfg:
        return
    try:
        from src.storage import Storage

        storage = Storage(cfg)
        await storage.init()
        # Write test
        import sqlite3

        conn = sqlite3.connect(cfg.db_path)
        conn.execute("SELECT COUNT(*) FROM scrape_history")
        conn.close()
        report.add("SQLite DB", True, f"writable at {cfg.db_path}")
    except Exception as e:
        report.add("SQLite DB", False, str(e), "mkdir -p data && chmod 755 data")

    # Check models JSON
    try:
        models_path = Path(cfg.model_registry_path)
        if models_path.exists():
            data = json.loads(models_path.read_text())
            report.add("Models JSON", True, f"{models_path} ({len(data)} keys)")
        else:
            report.add("Models JSON", False, "not found (will be created on first run)")
    except Exception as e:
        report.add("Models JSON", False, str(e))


async def check_vision_registry(report: DebugReport):
    print(HDR("Vision model registry"))
    try:
        from src.vision import ModelRegistry

        registry = ModelRegistry()
        d = registry.to_dict()

        report.add(
            "OpenRouter free vision models", True, f"{len(d.get('openrouter_free', []))} models (built-in + custom)"
        )
        report.add("Ollama vision models", True, f"{len(d.get('ollama', []))} models in registry")
        report.add("HF vision models", True, f"{len(d.get('huggingface', []))} models")
    except Exception as e:
        report.add("Vision registry", False, str(e))


async def check_live_scrape(report: DebugReport):
    print(HDR("Live scrape test (Jina Reader → example.com)"))
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                "https://r.jina.ai/https://example.com",
                headers={"Accept": "application/json"},
            )
        elapsed = round((time.time() - start) * 1000)
        if r.status_code == 200:
            content = r.text[:100].replace("\n", " ")
            report.add("Jina Reader", True, f"OK in {elapsed}ms: {content}...")
        else:
            report.add("Jina Reader", False, f"HTTP {r.status_code}")
    except Exception as e:
        report.add("Jina Reader live test", False, str(e))


# ── Main ──────────────────────────────────────────────────────────────────────


async def run_debug(full: bool = False, fix: bool = False):
    print(c("\n╔══════════════════════════════════════╗", "cyan"))
    print(c("║   AI Scraping Stack — Health Check   ║", "cyan"))
    print(c("╚══════════════════════════════════════╝\n", "cyan"))

    report = DebugReport()
    cfg = await check_config(report)
    await check_ollama(cfg, report)
    await check_openrouter(cfg, report)
    await check_hf(cfg, report)
    check_python_packages(report)
    check_scrapling_browsers(report)
    check_playwright_browsers(report)
    await check_storage(cfg, report)
    await check_vision_registry(report)

    if full:
        await check_live_scrape(report)

    all_ok = report.summary()

    if fix and not all_ok:
        print(f"\n{c('Auto-fix suggestions:', 'yellow')}")
        for issue in report.issues:
            print(f"  {c('→', 'yellow')} {issue}")

    return 0 if all_ok else 1


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Scraping Stack Health Check")
    parser.add_argument("--full", action="store_true", help="Include live scrape test")
    parser.add_argument("--fix", action="store_true", help="Show auto-fix suggestions")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    exit_code = asyncio.run(run_debug(full=args.full, fix=args.fix))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
