"""Assemble layered context (Session / Turn) into ContextBundle."""

from __future__ import annotations

import logging
from datetime import date

from app.agents.context.budget import apply_budget, strip_api_date_prefix
from app.agents.context.bundle import ContextBundle
from app.agents.context.compression import COMPRESSION_PROMPT, COMPRESSION_THRESHOLD
from app.agents.context.intent import classify_intent
from app.agents.context.layers import SessionContext, TurnContext
from app.core.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)


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
        system_date=date.today().isoformat(),
    )

    if intent.get("needs_memory"):
        try:
            from app.agents.memory import MemoryService

            result = await MemoryService().retrieve_for_injection(
                user_id=user_id,
                query=raw_message,
                category_priority=intent.get("priority_categories", []),
            )
            turn.memory_text = result.get("text", "")
            turn.memory_selected = result.get("selected", [])
        except Exception:
            logger.warning("记忆检索失败", exc_info=True)

    if settings.CONTEXT_USE_BUNDLE:
        try:
            from app.agents.config import create_checkpointer

            cp = create_checkpointer()
            checkpoint = cp.get({"configurable": {"thread_id": thread_id}})
            if checkpoint and checkpoint.get("channel_values"):
                messages = checkpoint["channel_values"].get("messages", [])
                if len(messages) > COMPRESSION_THRESHOLD:
                    recent = [
                        m.content
                        for m in messages[-20:]
                        if hasattr(m, "content") and m.content
                    ]
                    if recent:
                        conversation = "\n".join(recent[-10:])
                        model = get_chat_model()
                        resp = await model.ainvoke(
                            COMPRESSION_PROMPT.format(messages=conversation)
                        )
                        summary = resp.content if hasattr(resp, "content") else str(resp)
                        turn.history_summary = summary.strip()
        except Exception:
            logger.warning("历史压缩失败", exc_info=True)

    return turn


async def assemble_context(user_id: int, thread_id: str, message: str) -> ContextBundle:
    await build_session_context(user_id)
    turn = await build_turn_context(user_id, thread_id, message)
    return apply_budget(turn)
