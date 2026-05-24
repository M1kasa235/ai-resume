"""Memory CRUD operations."""

import logging

logger = logging.getLogger(__name__)


class MemoryRepositoryMixin:

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

    
