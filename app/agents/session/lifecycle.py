"""Conversation lifecycle: clear threads, checkpoints, and memory triggers."""

from __future__ import annotations

import logging

from app.core.async_tasks import create_context_task

logger = logging.getLogger(__name__)


async def clear_conversation_with_memory(isolated_thread_id: str, user_id: int) -> None:
    """Clear chat history, related sub-threads, round counters, and enqueue memory extract."""
    from app.agents.config import create_checkpointer
    from app.agents.context.threads import list_related_threads
    from app.agents.memory.ingest import run_memory_agent, set_memory_source
    from app.agents.orchestration.triggers import reset_round_counters
    from app.agents.session.checkpoint import checkpoint_transcript
    from app.agents.session.history import clear_chat_history

    summary = await checkpoint_transcript(isolated_thread_id, max_messages=20)
    await clear_chat_history(isolated_thread_id)

    checkpointer = create_checkpointer()
    related_threads = list_related_threads(isolated_thread_id, user_id)
    for tid in related_threads:
        try:
            await checkpointer.adelete_thread(tid)
        except Exception:
            logger.debug("清理子线程失败: %s", tid, exc_info=True)

    await reset_round_counters(isolated_thread_id, *related_threads)

    if summary:
        set_memory_source("thread_clear")
        create_context_task(
            run_memory_agent(
                summary,
                thread_id=f"{isolated_thread_id}_clear",
                event_type="thread_clear",
                sync_process=False,
            )
        )
