"""Periodic memory extraction triggers and round counters."""

import logging

from app.core.async_tasks import create_context_task
from app.core.context import require_current_user_id

logger = logging.getLogger(__name__)


async def reset_round_counters(*thread_ids: str):
    """Clear turn counters when conversation threads are deleted."""
    if not thread_ids:
        return
    from app.agents.memory import MemoryService

    await MemoryService().reset_thread_round_counters(*thread_ids)


async def maybe_trigger_memory_agent(thread_id: str):
    """每 N 轮对话自动触发记忆管理（fire-and-forget）"""
    from app.agents.memory import MemoryService
    from app.agents.memory.ingest import run_memory_agent, set_memory_source

    svc = MemoryService()
    if not await svc.increment_thread_round(thread_id):
        return

    uid = require_current_user_id()
    try:
        if uid:
            await MemoryService().decay(uid)
    except Exception:
        logger.debug("memory decay skipped", exc_info=True)

    try:
        from app.agents.session.checkpoint import checkpoint_transcript

        summary = await checkpoint_transcript(thread_id, max_messages=20, tail_messages=10)
        if summary:
            set_memory_source("auto")
            create_context_task(
                run_memory_agent(
                    summary,
                    thread_id=f"{thread_id}_auto",
                    event_type="auto_summary",
                    sync_process=False,
                )
            )
    except Exception:
        logger.debug("auto memory trigger failed", exc_info=True)
