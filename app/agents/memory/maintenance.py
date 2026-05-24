"""Memory maintenance: consolidation and decay."""

import logging
from datetime import datetime, timedelta

from app.agents.memory.constants import DECAY_DAYS

logger = logging.getLogger(__name__)


class MemoryMaintenanceMixin:

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
