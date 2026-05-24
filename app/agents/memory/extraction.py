"""LLM-based memory extraction and delta application."""

import asyncio
import hashlib
import json
import logging
from datetime import datetime

from app.agents.memory.constants import _EXTRACTION_PROMPT
from app.agents.memory.base import MemoryStoreBase

logger = logging.getLogger(__name__)


class MemoryExtractionMixin:

    @staticmethod
    def _sanitize_mem_key(category: str, mem_key: str, content: str) -> str:
        key = (mem_key or "").strip().lower().replace(" ", "_")
        if key:
            return key
        short = hashlib.md5((content or "").encode("utf-8")).hexdigest()[:8]
        return f"{category}_{short}"

    @staticmethod
    def _parse_delta(text: str) -> dict | None:
        content = MemoryStoreBase._strip_code_block(text)
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
        user_id: int | None = None,
    ) -> int:
        conn = await self._get_conn()
        batch_size = max(1, min(200, batch_size))
        if user_id is None:
            rows = await conn.execute_fetchall(
                """
                SELECT id FROM memory_events
                WHERE status IN ('pending', 'failed')
                  AND retry_count < ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (max_retries, batch_size),
            )
        else:
            rows = await conn.execute_fetchall(
                """
                SELECT id FROM memory_events
                WHERE user_id=?
                  AND status IN ('pending', 'failed')
                  AND retry_count < ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (user_id, max_retries, batch_size),
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

    
