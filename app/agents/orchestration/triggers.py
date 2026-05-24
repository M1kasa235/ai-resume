"""Periodic memory extraction triggers and round counters."""

import logging

from app.agents.config import create_checkpointer
from app.core.async_tasks import create_context_task
from app.core.context import require_current_user_id

logger = logging.getLogger(__name__)

AUTO_TRIGGER_ROUNDS = 10
_message_counter: dict[str, int] = {}


def reset_round_counters(*thread_ids: str):
    """Clear turn counters when conversation threads are deleted."""
    for tid in thread_ids:
        _message_counter.pop(tid, None)


async def maybe_trigger_memory_agent(thread_id: str):
    """每 N 轮对话自动触发记忆管理（fire-and-forget）"""
    _message_counter[thread_id] = _message_counter.get(thread_id, 0) + 1
    if _message_counter[thread_id] < AUTO_TRIGGER_ROUNDS:
        return
    _message_counter[thread_id] = 0

    from app.agents.memory import MemoryService
    from app.agents.memory.ingest import run_memory_agent, set_memory_source

    uid = require_current_user_id()
    try:
        if uid:
            await MemoryService().decay(uid)
    except Exception:
        logger.debug("memory decay skipped", exc_info=True)

    try:
        checkpoint = create_checkpointer().get({"configurable": {"thread_id": thread_id}})
        summary = ""
        if checkpoint and checkpoint.get("channel_values"):
            messages = checkpoint["channel_values"].get("messages", [])
            recent = [m.content for m in messages[-20:] if hasattr(m, "content") and m.content]
            summary = "\n".join(recent[-10:])
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
