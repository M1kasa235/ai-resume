"""Assemble layered context (Session / Turn) into ContextBundle."""

from __future__ import annotations

import hashlib
import json
import logging

from app.agents.context.budget import apply_budget, strip_api_date_prefix
from app.agents.context.bundle import ContextBundle
from app.agents.context.compression import COMPRESSION_PROMPT, COMPRESSION_THRESHOLD
from app.agents.context.intent import classify_intent
from app.agents.context.layers import SessionContext, TurnContext
from app.agents.context.temporal import reference_date
from app.core.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

MEMORY_RETRIEVAL_TTL = 60


def _query_hash(user_id: int, query: str) -> str:
    raw = f"{user_id}:{query}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def _cached_retrieve(ms, user_id: int, query: str, intent: dict) -> dict:
    """Redis-cached wrapper around MemoryService.retrieve_for_injection."""
    from app.core.redis import get_redis

    r = get_redis()
    cache_key = f"memory:retrieval:{_query_hash(user_id, query)}"

    if r is not None:
        try:
            data = await r.get(cache_key)
            if data:
                return json.loads(data)
        except Exception:
            pass

    result = await ms.retrieve_for_injection(
        user_id=user_id,
        query=query,
        category_priority=intent.get("priority_categories", []),
    )

    if r is not None:
        try:
            await r.setex(cache_key, MEMORY_RETRIEVAL_TTL, json.dumps(result, ensure_ascii=False))
        except Exception:
            pass

    return result


async def build_session_context(user_id: int) -> SessionContext:
    from app.agents.memory import MemoryService

    count = await MemoryService().count(user_id)
    return SessionContext(user_id=user_id, memory_count=count)


async def build_turn_context(user_id: int, thread_id: str, message: str) -> TurnContext:
    raw_message = strip_api_date_prefix(message)
    intent = classify_intent(raw_message)
    turn = TurnContext(
        thread_id=thread_id,
        raw_message=raw_message,
        intent=intent,
        system_date=reference_date(),
    )

    if intent.get("needs_memory"):
        try:
            from app.agents.memory import MemoryService

            result = await _cached_retrieve(
                MemoryService(), user_id, raw_message, intent
            )
            turn.memory_text = result.get("text", "")
            turn.memory_selected = result.get("selected", [])
        except Exception:
            logger.warning("记忆检索失败", exc_info=True)

    if settings.CONTEXT_USE_BUNDLE:
        try:
            from app.agents.config import create_checkpointer

            cp = create_checkpointer()
            checkpoint = await cp.aget({"configurable": {"thread_id": thread_id}})
            if checkpoint and checkpoint.get("channel_values"):
                messages = checkpoint["channel_values"].get("messages", [])
                if len(messages) > COMPRESSION_THRESHOLD:
                    recent = [
                        m.content
                        for m in messages[-20:]
                        if hasattr(m, "content") and m.content
                    ]
                    if recent:
                        cleaned = [_strip_for_history_compression(m) for m in recent[-10:]]
                        conversation = "\n".join(c for c in cleaned if c)
                        model = get_chat_model()
                        resp = await model.ainvoke(
                            COMPRESSION_PROMPT.format(
                                today=reference_date(),
                                messages=conversation,
                            )
                        )
                        summary = resp.content if hasattr(resp, "content") else str(resp)
                        turn.history_summary = summary.strip()
        except Exception:
            logger.warning("历史压缩失败", exc_info=True)

    return turn


def _strip_for_history_compression(content: str) -> str:
    """Remove injected context prefixes before history summarization."""
    from app.agents.session.message_display import normalize_user_message_for_display

    text = (content or "").strip()
    if not text:
        return ""
    if text.startswith("[用户偏好") or text.startswith("[系统上下文"):
        return normalize_user_message_for_display(text)
    if text.startswith("[对话历史摘要"):
        return ""
    return text[:800]


async def assemble_context(user_id: int, thread_id: str, message: str) -> ContextBundle:
    session = await build_session_context(user_id)
    turn = await build_turn_context(user_id, thread_id, message)
    bundle = apply_budget(turn)
    bundle.meta["memory_count"] = session.memory_count
    return bundle
