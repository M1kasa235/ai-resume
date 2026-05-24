"""Connection lifecycle, schema, and shared helpers."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

from app.agents.memory.constants import DECAY_DAYS, VALID_CATEGORIES

logger = logging.getLogger(__name__)


class MemoryStoreBase:
    """Shared state for memory mixins (singleton)."""

    _instance = None
    _context_cache: dict[int, str] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        from app.agents.memory.constants import MEMORY_DB_PATH
        self._db_path = db_path or MEMORY_DB_PATH
        self._conn: aiosqlite.Connection | None = None
        self._conn_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._initialized = True

    # -------------------------- 生命周期 / schema --------------------------

    @classmethod
    def invalidate_cache(cls, user_id: int):
        cls._context_cache.pop(user_id, None)

    @classmethod
    def get_cached_context(cls, user_id: int) -> str | None:
        return cls._context_cache.get(user_id)

    @classmethod
    def set_cached_context(cls, user_id: int, ctx: str):
        cls._context_cache[user_id] = ctx

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is not None:
            return self._conn
        async with self._conn_lock:
            if self._conn is not None:
                return self._conn
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = await aiosqlite.connect(self._db_path)
            self._conn.row_factory = aiosqlite.Row
            await self._ensure_table()
            return self._conn

    async def _ensure_columns(self, table: str, columns: dict[str, str]):
        conn = await self._get_conn()
        existing_rows = await conn.execute_fetchall(f"PRAGMA table_info({table})")
        existing = {r["name"] for r in existing_rows}
        for name, ddl in columns.items():
            if name in existing:
                continue
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

    async def _ensure_table(self):
        conn = self._conn or await self._get_conn()

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                category        TEXT NOT NULL,
                mem_key         TEXT NOT NULL,
                content         TEXT NOT NULL,
                importance      INTEGER DEFAULT 3,
                confidence      REAL DEFAULT 0.8,
                source          TEXT,
                source_event_id TEXT,
                status          TEXT DEFAULT 'active',
                version         INTEGER DEFAULT 1,
                access_count    INTEGER DEFAULT 0,
                last_accessed   TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime')),
                expires_at      TEXT,
                UNIQUE(user_id, category, mem_key)
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_events (
                id              TEXT PRIMARY KEY,
                user_id         INTEGER NOT NULL,
                thread_id       TEXT,
                event_type      TEXT NOT NULL,
                source          TEXT,
                payload         TEXT NOT NULL,
                idempotency_key TEXT UNIQUE,
                status          TEXT DEFAULT 'pending',
                retry_count     INTEGER DEFAULT 0,
                last_error      TEXT,
                result_json     TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime')),
                processed_at    TEXT
            )
            """
        )

        await self._ensure_columns(
            "user_memories",
            {
                "confidence": "REAL DEFAULT 0.8",
                "source_event_id": "TEXT",
                "status": "TEXT DEFAULT 'active'",
                "version": "INTEGER DEFAULT 1",
                "expires_at": "TEXT",
            },
        )
        await self._ensure_columns(
            "memory_events",
            {
                "source": "TEXT",
                "idempotency_key": "TEXT",
                "status": "TEXT DEFAULT 'pending'",
                "retry_count": "INTEGER DEFAULT 0",
                "last_error": "TEXT",
                "result_json": "TEXT",
                "processed_at": "TEXT",
            },
        )

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_user_status "
            "ON user_memories(user_id, status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_category "
            "ON user_memories(user_id, category, importance DESC)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_events_status "
            "ON memory_events(status, retry_count, created_at)"
        )
        await conn.commit()

    # -------------------------- 基础方法 --------------------------

    @staticmethod
    def _normalize_category(category: str) -> str:
        category = (category or "fact").strip().lower()
        return category if category in VALID_CATEGORIES else "fact"

    @staticmethod
    def _clamp_importance(importance: int) -> int:
        try:
            val = int(importance)
        except (TypeError, ValueError):
            return 3
        return max(1, min(5, val))

    @staticmethod
    def _clamp_confidence(confidence: float) -> float:
        try:
            val = float(confidence)
        except (TypeError, ValueError):
            return 0.8
        return max(0.0, min(1.0, val))

    def _compute_expire_at(self, importance: int) -> str | None:
        days = DECAY_DAYS.get(self._clamp_importance(importance), 90)
        if days < 0:
            return None
        return (datetime.now() + timedelta(days=days)).date().isoformat()

    @staticmethod
    def _safe_parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value[:19], fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _strip_code_block(text: str) -> str:
        value = (text or "").strip()
        if value.startswith("```"):
            lines = value.splitlines()
            value = "\n".join(lines[1:])
            if value.endswith("```"):
                value = value[:-3]
        return value.strip()

    