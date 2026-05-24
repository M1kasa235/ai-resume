"""Memory event queue (enqueue, retry, status)."""

import hashlib
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class MemoryEventsMixin:

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

    async def list_events(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> list[dict]:
        conn = await self._get_conn()
        limit = max(1, min(200, int(limit)))
        offset = max(0, int(offset))
        if status:
            rows = await conn.execute_fetchall(
                """
                SELECT * FROM memory_events
                WHERE user_id=? AND status=?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, status, limit, offset),
            )
        else:
            rows = await conn.execute_fetchall(
                """
                SELECT * FROM memory_events
                WHERE user_id=?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
        return [dict(r) for r in rows]

    async def get_event_stats(self, user_id: int) -> dict:
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            """
            SELECT status, COUNT(*) AS cnt
            FROM memory_events
            WHERE user_id=?
            GROUP BY status
            """,
            (user_id,),
        )
        by_status: dict[str, int] = {}
        total = 0
        for row in rows:
            status = str(row["status"])
            cnt = int(row["cnt"])
            by_status[status] = cnt
            total += cnt
        return {
            "total": total,
            "by_status": by_status,
            "pending_or_failed": by_status.get("pending", 0) + by_status.get("failed", 0),
            "dead_letter": by_status.get("dead_letter", 0),
        }

    async def retry_event(
        self,
        event_id: str,
        user_id: int | None = None,
        reset_retry_count: bool = True,
    ) -> dict | None:
        event = await self.get_event(event_id)
        if not event:
            return None
        if user_id is not None and int(event["user_id"]) != int(user_id):
            return None
        if event.get("status") == "processing":
            return event

        next_retry = 0 if reset_retry_count else int(event.get("retry_count") or 0)
        conn = await self._get_conn()
        async with self._write_lock:
            await conn.execute(
                """
                UPDATE memory_events
                SET status='pending',
                    retry_count=?,
                    last_error='',
                    updated_at=datetime('now','localtime'),
                    processed_at=NULL
                WHERE id=?
                """,
                (next_retry, event_id),
            )
            await conn.commit()
        return await self.get_event(event_id)

    async def retry_dead_letter_events(self, user_id: int, limit: int = 20) -> int:
        conn = await self._get_conn()
        limit = max(1, min(200, int(limit)))
        rows = await conn.execute_fetchall(
            """
            SELECT id FROM memory_events
            WHERE user_id=? AND status='dead_letter'
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (user_id, limit),
        )
        event_ids = [str(r["id"]) for r in rows]
        if not event_ids:
            return 0

        placeholders = ",".join("?" for _ in event_ids)
        async with self._write_lock:
            await conn.execute(
                f"""
                UPDATE memory_events
                SET status='pending',
                    retry_count=0,
                    last_error='',
                    updated_at=datetime('now','localtime'),
                    processed_at=NULL
                WHERE id IN ({placeholders})
                """,
                event_ids,
            )
            await conn.commit()
        return len(event_ids)

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

    
