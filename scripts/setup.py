#!/usr/bin/env python3
"""
scripts/setup.py — Automatic project setup
============================================
Creates .env from .env.example, installs dependencies, pulls models.

Usage:
    python scripts/setup.py
    python scripts/setup.py --no-ollama  # Skip Ollama setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check, capture_output=False)


def create_env():
    """Create .env from .env.example if it doesn't exist."""
    env_path = Path(".env")
    example_path = Path(".env.example")

    if env_path.exists():
        print("  ✓ .env already exists")
        return

    if not example_path.exists():
        print("  ✗ .env.example not found")
        return

    shutil.copy(example_path, env_path)
    print("  ✓ Created .env from .env.example")
    print("  → Edit .env with your API keys")


def install_deps():
    """Install Python dependencies."""
    print("\n[2/4] Installing dependencies...")
    run("pip install -r requirements.txt")
    print("  ✓ Dependencies installed")


def install_scrapling():
    """Install Scrapling browsers."""
    print("\n[3/4] Installing Scrapling browsers...")
    try:
        run("scrapling install")
        print("  ✓ Scrapling browsers installed")
    except subprocess.CalledProcessError:
        print("  ⚠ Scrapling install failed (optional)")


def pull_ollama_models(no_ollama: bool = False):
    """Pull recommended Ollama models."""
    if no_ollama:
        print("\n[4/4] Skipping Ollama setup (--no-ollama)")
        return

    print("\n[4/4] Pulling Ollama models...")
    models = ["llama3.2", "qwen2.5"]

    # Check if Ollama is running
    try:
        import httpx

        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code != 200:
            print("  ⚠ Ollama not running. Skip model pull or run: ollama serve")
            return
    except Exception:
        print("  ⚠ Ollama not running. Skip model pull or run: ollama serve")
        return

    for model in models:
        print(f"  Pulling {model}...")
        try:
            run(f"ollama pull {model}")
            print(f"  ✓ {model} pulled")
        except subprocess.CalledProcessError:
            print(f"  ⚠ Failed to pull {model}")


def main():
    no_ollama = "--no-ollama" in sys.argv

    print("=" * 50)
    print("  AI Scraping Stack — Setup")
    print("=" * 50)

    create_env()
    install_deps()
    install_scrapling()
    pull_ollama_models(no_ollama)

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Edit .env with your API keys")
    print("  2. uvicorn api:app --reload --port 8100")
    print("  3. Open landing.html in browser")


if __name__ == "__main__":
    main()
