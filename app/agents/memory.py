"""长期记忆服务：事件驱动提取、持久化和检索注入。"""

import asyncio
import hashlib
import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import aiosqlite

logger = logging.getLogger(__name__)

MEMORY_DB_PATH = str(
    Path(__file__).resolve().parent.parent / "db" / "agent_sessions" / "memory.db"
)

VALID_CATEGORIES = {"fact", "preference", "insight", "goal"}
CATEGORY_ORDER = ["fact", "preference", "insight", "goal"]
CATEGORY_LABELS = {"fact": "技能事实", "preference": "偏好", "insight": "洞察", "goal": "目标"}

# 衰减周期：importance -> 保留天数(-1 表示不过期)
DECAY_DAYS = {1: 7, 2: 30, 3: 90, 4: 180, 5: -1}

# query-aware 注入预算
CONTEXT_MAX_CHARS = 520
CATEGORY_QUOTA = {"fact": 0.40, "preference": 0.30, "insight": 0.20, "goal": 0.10}

# 领域关键词映射：query 出现左侧词时，会扩展右侧召回词
DOMAIN_MAP: dict[str, list[str]] = {
    "前端": ["react", "vue", "angular", "javascript", "typescript", "css", "html", "nextjs", "vite"],
    "后端": ["python", "java", "go", "fastapi", "django", "spring", "数据库", "redis", "kafka"],
    "简历": ["诊断", "优化", "项目", "教育", "工作经历", "匹配", "润色"],
    "面试": ["行为面试", "自我介绍", "八股文", "模拟", "评估"],
    "岗位": ["推荐", "职位", "招聘", "投递", "内推"],
    "薪资": ["年薪", "月薪", "待遇", "涨薪", "谈薪", "k"],
    "城市": ["北京", "上海", "深圳", "广州", "杭州", "成都", "远程"],
}

_EXTRACTION_PROMPT = """你是长期记忆抽取器。请从对话中提取“关于用户且可跨会话复用”的信息。

已有记忆：
{existing_summary}

规则：
1) 只保留重要度>=3的信息（3=有参考价值，4=重要，5=核心）。
2) 同一事实若出现更新，使用 delete 标注旧 key，并在 upsert 给出新内容。
3) content 精炼，不超过 40 字，禁止把助手建议当成用户记忆。
4) fact/insight 通常 append；preference/goal 通常 overwrite。
5) 输出必须是 JSON，不要 markdown 代码块。

输出格式：
{{
  "upsert": [
    {{
      "category": "fact|preference|insight|goal",
      "mem_key": "snake_case_key",
      "content": "记忆内容",
      "importance": 3,
      "confidence": 0.85,
      "mode": "append|overwrite"
    }}
  ],
  "delete": ["category/mem_key", "mem_key_only"]
}}
"""


class MemoryService:
    """事件驱动长期记忆服务（单例）。"""

    _instance = None
    _context_cache: dict[int, str] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = MEMORY_DB_PATH):
        if self._initialized:
            return
        self._db_path = db_path
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

    # -------------------------- CRUD（兼容旧接口） --------------------------

    async def upsert(
        self,
        user_id: int,
        category: str,
        mem_key: str,
        content: str,
        importance: int = 3,
        source: str = "",
        confidence: float = 0.8,
        source_event_id: str | None = None,
    ):
        category = self._normalize_category(category)
        mem_key = (mem_key or "").strip()
        content = (content or "").strip()
        if not mem_key or not content:
            return
        importance = self._clamp_importance(importance)
        confidence = self._clamp_confidence(confidence)
        expires_at = self._compute_expire_at(importance)

        conn = await self._get_conn()
        async with self._write_lock:
            row = await conn.execute_fetchall(
                """
                SELECT id, version, content, importance
                FROM user_memories
                WHERE user_id=? AND category=? AND mem_key=?
                LIMIT 1
                """,
                (user_id, category, mem_key),
            )
            if row:
                old = row[0]
                changed = (
                    (old["content"] or "") != content
                    or int(old["importance"] or 3) != importance
                )
                version = int(old["version"] or 1) + (1 if changed else 0)
                await conn.execute(
                    """
                    UPDATE user_memories
                    SET content=?,
                        importance=?,
                        confidence=?,
                        source=?,
                        source_event_id=?,
                        status='active',
                        version=?,
                        expires_at=?,
                        updated_at=datetime('now','localtime')
                    WHERE id=?
                    """,
                    (
                        content,
                        importance,
                        confidence,
                        source,
                        source_event_id,
                        version,
                        expires_at,
                        old["id"],
                    ),
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO user_memories
                    (user_id, category, mem_key, content, importance, confidence,
                     source, source_event_id, status, version, expires_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, ?, datetime('now','localtime'), datetime('now','localtime'))
                    """,
                    (
                        user_id,
                        category,
                        mem_key,
                        content,
                        importance,
                        confidence,
                        source,
                        source_event_id,
                        expires_at,
                    ),
                )
            await conn.commit()
        self.invalidate_cache(user_id)

    async def delete(self, user_id: int, category: str, mem_key: str):
        conn = await self._get_conn()
        async with self._write_lock:
            await conn.execute(
                """
                UPDATE user_memories
                SET status='deleted', updated_at=datetime('now','localtime')
                WHERE user_id=? AND category=? AND mem_key=?
                """,
                (user_id, self._normalize_category(category), mem_key),
            )
            await conn.commit()
        self.invalidate_cache(user_id)

    async def _delete_by_key(self, user_id: int, key: str):
        conn = await self._get_conn()
        async with self._write_lock:
            if "/" in key:
                cat, mk = key.split("/", 1)
                await conn.execute(
                    """
                    UPDATE user_memories
                    SET status='deleted', updated_at=datetime('now','localtime')
                    WHERE user_id=? AND category=? AND mem_key=?
                    """,
                    (user_id, self._normalize_category(cat), mk),
                )
            else:
                await conn.execute(
                    """
                    UPDATE user_memories
                    SET status='deleted', updated_at=datetime('now','localtime')
                    WHERE user_id=? AND mem_key=?
                    """,
                    (user_id, key),
                )
            await conn.commit()
        self.invalidate_cache(user_id)

    async def get_all(self, user_id: int, include_inactive: bool = False) -> list[dict]:
        conn = await self._get_conn()
        if include_inactive:
            rows = await conn.execute_fetchall(
                """
                SELECT * FROM user_memories
                WHERE user_id=?
                ORDER BY importance DESC, updated_at DESC
                """,
                (user_id,),
            )
        else:
            rows = await conn.execute_fetchall(
                """
                SELECT * FROM user_memories
                WHERE user_id=? AND status='active'
                ORDER BY importance DESC, updated_at DESC
                """,
                (user_id,),
            )
        return [dict(r) for r in rows]

    async def count(self, user_id: int, include_inactive: bool = False) -> int:
        conn = await self._get_conn()
        if include_inactive:
            row = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM user_memories WHERE user_id=?",
                (user_id,),
            )
        else:
            row = await conn.execute_fetchall(
                "SELECT COUNT(*) AS cnt FROM user_memories WHERE user_id=? AND status='active'",
                (user_id,),
            )
        return int(row[0]["cnt"]) if row else 0

    async def bump_access(self, user_id: int, memory_ids: list[int] | None = None):
        conn = await self._get_conn()
        async with self._write_lock:
            if memory_ids:
                placeholders = ",".join("?" for _ in memory_ids)
                await conn.execute(
                    f"""
                    UPDATE user_memories
                    SET access_count=access_count+1,
                        last_accessed=datetime('now','localtime')
                    WHERE user_id=? AND id IN ({placeholders})
                    """,
                    [user_id, *memory_ids],
                )
            else:
                await conn.execute(
                    """
                    UPDATE user_memories
                    SET access_count=access_count+1,
                        last_accessed=datetime('now','localtime')
                    WHERE user_id=? AND status='active'
                    """,
                    (user_id,),
                )
            await conn.commit()

    # -------------------------- 检索与注入 --------------------------

    @staticmethod
    def _compute_relevance(query: str, mem: dict) -> float:
        if not query:
            return 1.0
        content = (mem.get("content") or "").lower()
        q = query.lower()

        # 内容匹配
        terms: set[str] = set()
        for domain, aliases in DOMAIN_MAP.items():
            if domain in q:
                terms.add(domain)
                terms.update(aliases)
        kw_hit = any(t in content for t in terms) if terms else False
        q_grams = {q[i : i + 2] for i in range(len(q) - 1)} if len(q) >= 2 else {q}
        c_grams = {content[i : i + 2] for i in range(len(content) - 1)} if len(content) >= 2 else {content}
        gram_overlap = len(q_grams & c_grams) / max(1, len(q_grams))
        content_score = max(gram_overlap, 0.75 if kw_hit else 0.0)

        # 重要度
        importance = max(1, min(5, int(mem.get("importance") or 3)))
        importance_score = importance / 5.0

        # 时效
        updated = MemoryService._safe_parse_dt(mem.get("updated_at"))
        if updated is None:
            recency = 0.5
        else:
            days = max(0, (datetime.now() - updated).days)
            recency = 1.0 if days <= 7 else max(0.25, math.exp(-(days - 7) / 45))

        # 稳定度（被检索次数）
        access = int(mem.get("access_count") or 0)
        stability = min(1.0, access / 8.0)

        score = 0.45 * content_score + 0.20 * importance_score + 0.20 * recency + 0.15 * stability
        return max(0.0, min(1.0, score))

    async def retrieve_for_injection(
        self,
        user_id: int,
        query: str = "",
        category_priority: list[str] | None = None,
        budget_chars: int = CONTEXT_MAX_CHARS,
        max_items: int = 12,
        min_score: float = 0.18,
    ) -> dict:
        memories = await self.get_all(user_id)
        if not memories:
            return {"text": "", "selected": [], "truncated": 0, "total_candidates": 0}

        scored: list[tuple[float, dict]] = []
        for mem in memories:
            score = self._compute_relevance(query, mem)
            if query and score < min_score:
                continue
            scored.append((score, mem))

        if not scored:
            return {"text": "", "selected": [], "truncated": 0, "total_candidates": 0}

        scored.sort(
            key=lambda x: (
                x[0],
                int(x[1].get("importance") or 0),
                x[1].get("updated_at") or "",
            ),
            reverse=True,
        )

        groups: dict[str, list[tuple[float, dict]]] = {c: [] for c in CATEGORY_ORDER}
        for item in scored:
            category = self._normalize_category(item[1].get("category", "fact"))
            groups[category].append(item)

        ordered_categories = []
        if category_priority:
            for cat in category_priority:
                nc = self._normalize_category(cat)
                if nc not in ordered_categories:
                    ordered_categories.append(nc)
        for cat in CATEGORY_ORDER:
            if cat not in ordered_categories:
                ordered_categories.append(cat)

        selected: list[dict] = []
        selected_ids: list[int] = []
        used_chars = 0
        truncated = 0

        for cat in ordered_categories:
            items = groups.get(cat, [])
            if not items:
                continue
            quota = int(budget_chars * CATEGORY_QUOTA.get(cat, 0.25))
            quota = max(60, quota)
            quota_chars = 0

            for score, mem in items:
                text = (mem.get("content") or "").strip()
                if not text:
                    continue
                piece_len = len(text) + 3
                if len(selected) >= max_items or used_chars + piece_len > budget_chars:
                    truncated += 1
                    continue
                if quota_chars + piece_len > quota:
                    truncated += 1
                    continue
                selected.append(
                    {
                        "id": mem.get("id"),
                        "category": cat,
                        "mem_key": mem.get("mem_key"),
                        "content": text,
                        "importance": int(mem.get("importance") or 3),
                        "score": round(score, 4),
                    }
                )
                if mem.get("id") is not None:
                    selected_ids.append(int(mem["id"]))
                used_chars += piece_len
                quota_chars += piece_len

        # 兜底：query 命中过窄时，补充一条最高重要记忆
        if query and not selected:
            top = sorted(memories, key=lambda m: int(m.get("importance") or 0), reverse=True)[:1]
            for mem in top:
                text = (mem.get("content") or "").strip()
                if text:
                    selected.append(
                        {
                            "id": mem.get("id"),
                            "category": self._normalize_category(mem.get("category", "fact")),
                            "mem_key": mem.get("mem_key"),
                            "content": text,
                            "importance": int(mem.get("importance") or 3),
                            "score": 0.0,
                        }
                    )
                    if mem.get("id") is not None:
                        selected_ids.append(int(mem["id"]))

        by_category: dict[str, list[str]] = {c: [] for c in CATEGORY_ORDER}
        for item in selected:
            by_category[item["category"]].append(item["content"])

        lines = []
        for cat in ordered_categories:
            items = by_category.get(cat, [])
            if items:
                lines.append(f"[{CATEGORY_LABELS[cat]}: {' | '.join(items)}]")
        if truncated:
            lines.append(f"[还有{truncated}条候选记忆未注入]")

        if selected_ids:
            await self.bump_access(user_id, selected_ids)

        return {
            "text": "\n".join(lines),
            "selected": selected,
            "truncated": truncated,
            "total_candidates": len(scored),
        }

    async def format_context(self, user_id: int, query: str = "") -> str:
        """兼容旧接口：返回注入字符串。"""
        if not query:
            cached = self.get_cached_context(user_id)
            if cached is not None:
                return cached
        result = await self.retrieve_for_injection(user_id, query=query)
        text = result.get("text", "")
        if text and not query:
            self.set_cached_context(user_id, text)
        return text

    # -------------------------- 事件队列 --------------------------

    @staticmethod
    def _build_idempotency_key(
        user_id: int,
        thread_id: str,
        event_type: str,
        source: str,
        payload_text: str,
    ) -> str:
        raw = f"{user_id}|{thread_id}|{event_type}|{source}|{payload_text[:3000]}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    async def enqueue_event(
        self,
        user_id: int,
        thread_id: str,
        event_type: str,
        payload: dict | str,
        source: str = "",
        idempotency_key: str | None = None,
    ) -> str:
        conn = await self._get_conn()
        payload_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        idem_key = idempotency_key or self._build_idempotency_key(
            user_id=user_id,
            thread_id=thread_id,
            event_type=event_type,
            source=source,
            payload_text=payload_text,
        )

        async with self._write_lock:
            exists = await conn.execute_fetchall(
                "SELECT id FROM memory_events WHERE idempotency_key=? LIMIT 1",
                (idem_key,),
            )
            if exists:
                return str(exists[0]["id"])

            event_id = str(uuid4())
            await conn.execute(
                """
                INSERT INTO memory_events
                (id, user_id, thread_id, event_type, source, payload, idempotency_key,
                 status, retry_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, datetime('now','localtime'), datetime('now','localtime'))
                """,
                (event_id, user_id, thread_id, event_type, source, payload_text, idem_key),
            )
            await conn.commit()
        return event_id

    async def get_event(self, event_id: str) -> dict | None:
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            "SELECT * FROM memory_events WHERE id=? LIMIT 1",
            (event_id,),
        )
        return dict(rows[0]) if rows else None

    async def list_events(self, user_id: int, limit: int = 20) -> list[dict]:
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            """
            SELECT * FROM memory_events
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, max(1, min(100, int(limit)))),
        )
        return [dict(r) for r in rows]

    async def _mark_event_status(
        self,
        event_id: str,
        status: str,
        retry_count: int | None = None,
        last_error: str | None = None,
        result_json: str | None = None,
        processed: bool = False,
    ):
        conn = await self._get_conn()
        sets = ["status=?", "updated_at=datetime('now','localtime')"]
        values: list = [status]
        if retry_count is not None:
            sets.append("retry_count=?")
            values.append(retry_count)
        if last_error is not None:
            sets.append("last_error=?")
            values.append(last_error[:500])
        if result_json is not None:
            sets.append("result_json=?")
            values.append(result_json)
        if processed:
            sets.append("processed_at=datetime('now','localtime')")
        values.append(event_id)
        async with self._write_lock:
            await conn.execute(
                f"UPDATE memory_events SET {', '.join(sets)} WHERE id=?",
                values,
            )
            await conn.commit()

    # -------------------------- 提取与应用 --------------------------

    @staticmethod
    def _sanitize_mem_key(category: str, mem_key: str, content: str) -> str:
        key = (mem_key or "").strip().lower().replace(" ", "_")
        if key:
            return key
        short = hashlib.md5((content or "").encode("utf-8")).hexdigest()[:8]
        return f"{category}_{short}"

    @staticmethod
    def _parse_delta(text: str) -> dict | None:
        content = MemoryService._strip_code_block(text)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("记忆提取 JSON 解析失败: %s", content[:200])
            return None
        if not isinstance(parsed, dict):
            return None
        if "upsert" not in parsed and "delete" not in parsed:
            return None
        return parsed

    def _normalize_delta(self, delta: dict) -> dict:
        upsert_raw = delta.get("upsert") or []
        delete_raw = delta.get("delete") or []
        normalized_upsert = []

        for item in upsert_raw[:8]:
            if not isinstance(item, dict):
                continue
            category = self._normalize_category(item.get("category", "fact"))
            content = (item.get("content") or "").strip()
            if not content:
                continue
            mem_key = self._sanitize_mem_key(category, item.get("mem_key", ""), content)
            importance = self._clamp_importance(item.get("importance", 3))
            confidence = self._clamp_confidence(item.get("confidence", 0.8))
            mode = (item.get("mode") or "").strip().lower()
            if mode not in {"append", "overwrite"}:
                mode = "append" if category in {"fact", "insight"} else "overwrite"

            normalized_upsert.append(
                {
                    "category": category,
                    "mem_key": mem_key,
                    "content": content[:80],
                    "importance": importance,
                    "confidence": confidence,
                    "mode": mode,
                }
            )

        normalized_delete = []
        for item in delete_raw[:8]:
            if isinstance(item, str) and item.strip():
                normalized_delete.append(item.strip())

        return {"upsert": normalized_upsert, "delete": normalized_delete}

    async def _extract_delta_from_transcript(
        self,
        user_id: int,
        transcript: str,
        source: str,
        llm,
    ) -> dict | None:
        existing = await self.get_all(user_id)
        if existing:
            summary = "; ".join(
                f"{m['category']}/{m['mem_key']}={m['content']}"
                for m in existing[:30]
            )
        else:
            summary = "无"

        prompt = _EXTRACTION_PROMPT.format(existing_summary=summary)
        full_prompt = f"{prompt}\n\n来源：{source}\n对话内容：\n{(transcript or '')[-5000:]}"

        try:
            resp = await asyncio.wait_for(llm.ainvoke(full_prompt), timeout=35)
            text = resp.content if hasattr(resp, "content") else str(resp)
            raw = self._parse_delta(text)
            if not raw:
                return None
            return self._normalize_delta(raw)
        except asyncio.TimeoutError:
            logger.warning("记忆提取超时")
            return None
        except Exception:
            logger.warning("记忆提取失败", exc_info=True)
            return None

    async def _apply_delta(
        self,
        user_id: int,
        source: str,
        source_event_id: str,
        delta: dict,
    ) -> dict:
        deleted = 0
        upserted = 0

        for key in delta.get("delete", []):
            await self._delete_by_key(user_id, key)
            deleted += 1

        for item in delta.get("upsert", []):
            category = item["category"]
            mem_key = item["mem_key"]
            if item.get("mode") == "append":
                suffix = datetime.now().strftime("%Y%m%d%H%M%S")
                mem_key = f"{mem_key}_{suffix}"
            await self.upsert(
                user_id=user_id,
                category=category,
                mem_key=mem_key,
                content=item["content"],
                importance=item["importance"],
                confidence=item["confidence"],
                source=source,
                source_event_id=source_event_id,
            )
            upserted += 1

        self.invalidate_cache(user_id)
        return {"upserted": upserted, "deleted": deleted}

    async def process_event(
        self,
        event_id: str,
        llm=None,
        max_retries: int = 3,
    ) -> dict | None:
        event = await self.get_event(event_id)
        if not event:
            return None
        if event.get("status") == "done":
            if event.get("result_json"):
                try:
                    return json.loads(event["result_json"])
                except json.JSONDecodeError:
                    return None
            return None
        if event.get("status") == "dead_letter":
            return None

        await self._mark_event_status(event_id, "processing")
        if llm is None:
            from app.core.llm import get_chat_model

            llm = get_chat_model()

        try:
            payload_text = event.get("payload") or ""
            payload = {}
            if payload_text:
                try:
                    payload = json.loads(payload_text)
                except json.JSONDecodeError:
                    payload = {"transcript": payload_text}
            transcript = (
                payload.get("transcript")
                or payload.get("summary")
                or payload.get("content")
                or payload_text
            )
            source = payload.get("source") or event.get("source") or "unknown"

            delta = await self._extract_delta_from_transcript(
                user_id=int(event["user_id"]),
                transcript=transcript,
                source=source,
                llm=llm,
            )
            apply_result = {"upserted": 0, "deleted": 0}
            if delta:
                apply_result = await self._apply_delta(
                    user_id=int(event["user_id"]),
                    source=source,
                    source_event_id=event_id,
                    delta=delta,
                )
            result = {
                "event_id": event_id,
                "delta": delta,
                "upserted": apply_result["upserted"],
                "deleted": apply_result["deleted"],
            }
            await self._mark_event_status(
                event_id,
                "done",
                retry_count=int(event.get("retry_count") or 0),
                last_error="",
                result_json=json.dumps(result, ensure_ascii=False),
                processed=True,
            )
            return result
        except Exception as exc:
            retry_count = int(event.get("retry_count") or 0) + 1
            status = "dead_letter" if retry_count >= max_retries else "failed"
            await self._mark_event_status(
                event_id,
                status,
                retry_count=retry_count,
                last_error=str(exc),
            )
            logger.warning("处理记忆事件失败: id=%s retry=%s", event_id, retry_count, exc_info=True)
            return None

    async def process_pending_events(
        self,
        llm=None,
        batch_size: int = 20,
        max_retries: int = 3,
    ) -> int:
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            """
            SELECT id FROM memory_events
            WHERE status IN ('pending', 'failed')
              AND retry_count < ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (max_retries, max(1, min(100, batch_size))),
        )
        count = 0
        for row in rows:
            result = await self.process_event(row["id"], llm=llm, max_retries=max_retries)
            if result is not None:
                count += 1
        return count

    async def extract_from_transcript(
        self,
        user_id: int,
        transcript: str,
        source: str,
        llm,
    ) -> dict | None:
        """兼容旧接口：现在走事件队列单写路径。"""
        event_id = await self.enqueue_event(
            user_id=user_id,
            thread_id=f"user_{user_id}_manual_extract",
            event_type="manual_extract",
            payload={"transcript": transcript, "source": source},
            source=source,
        )
        result = await self.process_event(event_id, llm=llm)
        if not result:
            return None
        return result.get("delta")

    # -------------------------- 维护 --------------------------

    async def consolidate(self, user_id: int, llm=None):
        """轻量整合：同类重复内容只保留一条活跃项。"""
        memories = await self.get_all(user_id)
        if len(memories) <= 50:
            return
        conn = await self._get_conn()
        seen: set[tuple[str, str]] = set()
        archived = 0
        async with self._write_lock:
            for mem in sorted(
                memories,
                key=lambda m: (int(m.get("importance") or 0), m.get("updated_at") or ""),
                reverse=True,
            ):
                fp = (
                    self._normalize_category(mem.get("category", "fact")),
                    (mem.get("content") or "").strip().lower(),
                )
                if fp in seen:
                    await conn.execute(
                        """
                        UPDATE user_memories
                        SET status='archived', updated_at=datetime('now','localtime')
                        WHERE id=?
                        """,
                        (mem["id"],),
                    )
                    archived += 1
                else:
                    seen.add(fp)
            await conn.commit()
        if archived:
            logger.info("记忆整合完成: user=%s archived=%s", user_id, archived)
            self.invalidate_cache(user_id)

    async def decay(self, user_id: int):
        conn = await self._get_conn()
        today = datetime.now().date().isoformat()
        total = 0
        async with self._write_lock:
            # 优先使用 expires_at 精确过期
            cursor = await conn.execute(
                """
                UPDATE user_memories
                SET status='expired', updated_at=datetime('now','localtime')
                WHERE user_id=? AND status='active'
                  AND expires_at IS NOT NULL AND expires_at < ?
                """,
                (user_id, today),
            )
            total += cursor.rowcount

            # 兼容历史行（无 expires_at）：按 importance + created_at 过期
            now = datetime.now()
            for imp, days in DECAY_DAYS.items():
                if days < 0:
                    continue
                cutoff = (now - timedelta(days=days)).date().isoformat()
                cursor = await conn.execute(
                    """
                    UPDATE user_memories
                    SET status='expired', updated_at=datetime('now','localtime')
                    WHERE user_id=? AND status='active' AND importance=? AND created_at < ?
                      AND (expires_at IS NULL OR expires_at = '')
                    """,
                    (user_id, imp, cutoff),
                )
                total += cursor.rowcount
            await conn.commit()

        if total:
            logger.info("memory decay: user=%s expired=%s", user_id, total)
            self.invalidate_cache(user_id)

    async def decay_all(self):
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            "SELECT DISTINCT user_id FROM user_memories WHERE status='active'"
        )
        for row in rows:
            await self.decay(int(row["user_id"]))
