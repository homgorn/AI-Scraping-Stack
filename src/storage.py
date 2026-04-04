"""
src/storage.py — SQLite history + JSON model registry
=====================================================
Persists every scrape result and model configuration.

Usage:
    from src.storage import Storage
    from src.config import get_settings
    storage = Storage(get_settings())
    await storage.init()
    await storage.save_result(scrape_response)
    history = await storage.get_history(limit=50)
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import Settings
from src.models import ScrapeResponse, HistoryEntry, StatsResponse


class Storage:
    """SQLite-backed storage for scrape history and model registry."""

    def __init__(self, settings: Settings):
        self.cfg = settings
        self._conn: Optional[sqlite3.Connection] = None

    async def init(self):
        """Initialize DB and create tables."""
        Path(self.cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.cfg.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                provider TEXT,
                task TEXT,
                model_used TEXT,
                cost_usd REAL DEFAULT 0,
                elapsed_ms INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                error TEXT,
                markdown TEXT,
                analysis TEXT
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url ON scrape_history(url)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON scrape_history(timestamp)
        """)
        self._conn.commit()
        self._init_model_registry()

    def _init_model_registry(self):
        """Initialize JSON model registry."""
        path = Path(self.cfg.model_registry_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                json.dumps(
                    {
                        "openrouter_models": [],
                        "custom_apis": [],
                        "config_overrides": {},
                    },
                    indent=2,
                )
            )

    async def save_result(self, result: ScrapeResponse, task: str = ""):
        """Save a scrape result to history."""
        if self._conn is None:
            await self.init()
        self._conn.execute(
            """INSERT INTO scrape_history
               (url, provider, task, model_used, cost_usd, elapsed_ms, timestamp, error, markdown, analysis)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.url,
                result.provider,
                task,
                result.model_used,
                result.cost_usd,
                result.elapsed_ms,
                datetime.utcnow().isoformat(),
                result.error,
                result.markdown[:10000] if result.markdown else "",
                result.analysis[:5000] if result.analysis else "",
            ),
        )
        self._conn.commit()

    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        url_filter: str = "",
    ) -> list[HistoryEntry]:
        """Get scrape history with optional filtering."""
        if self._conn is None:
            await self.init()

        query = "SELECT * FROM scrape_history"
        params: list = []
        if url_filter:
            query += " WHERE url LIKE ?"
            params.append(f"%{url_filter}%")
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        return [
            HistoryEntry(
                id=r["id"],
                url=r["url"],
                provider=r["provider"] or "",
                task=r["task"] or "",
                model_used=r["model_used"] or "",
                cost_usd=r["cost_usd"] or 0.0,
                elapsed_ms=r["elapsed_ms"] or 0,
                timestamp=r["timestamp"],
                error=r["error"],
            )
            for r in rows
        ]

    async def get_stats(self) -> StatsResponse:
        """Get aggregate statistics."""
        if self._conn is None:
            await self.init()

        row = self._conn.execute(
            """SELECT
                COUNT(*) as total,
                COALESCE(SUM(cost_usd), 0) as total_cost,
                COALESCE(AVG(elapsed_ms), 0) as avg_ms,
                SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as success_count
               FROM scrape_history"""
        ).fetchone()

        total = row["total"] or 0
        if total == 0:
            return StatsResponse()

        # Top providers
        providers = self._conn.execute(
            "SELECT provider, COUNT(*) as cnt FROM scrape_history GROUP BY provider ORDER BY cnt DESC LIMIT 5"
        ).fetchall()

        # Top models
        models = self._conn.execute(
            "SELECT model_used, COUNT(*) as cnt FROM scrape_history WHERE model_used != '' GROUP BY model_used ORDER BY cnt DESC LIMIT 5"
        ).fetchall()

        return StatsResponse(
            total_scrapes=total,
            total_cost_usd=round(row["total_cost"], 4),
            avg_elapsed_ms=round(row["avg_ms"], 1),
            top_providers={r["provider"]: r["cnt"] for r in providers},
            top_models={r["model_used"]: r["cnt"] for r in models},
            success_rate=round((row["success_count"] / total) * 100, 1),
        )

    # ── Model registry ──────────────────────────────────────────────────────

    def load_model_registry(self) -> dict:
        """Load model registry from JSON."""
        path = Path(self.cfg.model_registry_path)
        if path.exists():
            return json.loads(path.read_text())
        return {"openrouter_models": [], "custom_apis": [], "config_overrides": {}}

    def save_model_registry(self, data: dict):
        """Save model registry to JSON."""
        Path(self.cfg.model_registry_path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )

    def add_openrouter_model(self, model: dict):
        """Add custom OpenRouter model."""
        reg = self.load_model_registry()
        reg["openrouter_models"].append(model)
        self.save_model_registry(reg)

    def remove_openrouter_model(self, model_id: str):
        """Remove custom OpenRouter model."""
        reg = self.load_model_registry()
        reg["openrouter_models"] = [
            m for m in reg["openrouter_models"] if m.get("model_id") != model_id
        ]
        self.save_model_registry(reg)

    def add_custom_api(self, api: dict):
        """Add custom OpenAI-compatible API."""
        reg = self.load_model_registry()
        reg["custom_apis"].append(api)
        self.save_model_registry(reg)

    def remove_custom_api(self, name: str):
        """Remove custom API."""
        reg = self.load_model_registry()
        reg["custom_apis"] = [a for a in reg["custom_apis"] if a.get("name") != name]
        self.save_model_registry(reg)

    def get_config_overrides(self) -> dict:
        """Get runtime config overrides."""
        return self.load_model_registry().get("config_overrides", {})

    def save_config_override(self, key: str, value):
        """Save a config override."""
        reg = self.load_model_registry()
        reg["config_overrides"][key] = value
        self.save_model_registry(reg)
