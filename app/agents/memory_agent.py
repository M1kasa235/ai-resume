"""Memory ingestion entrypoint: enqueue + process."""

import asyncio
import contextvars
import logging

from app.agents.memory import MemoryService
from app.core.context import get_trace_id, get_current_user_id
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

_memory_source: contextvars.ContextVar[str] = contextvars.ContextVar(
    "memory_source", default="unknown"
)


def set_memory_source(source: str):
    _memory_source.set(source)


async def run_memory_agent(
    dialogue_summary: str,
    thread_id: str = "memory",
    event_type: str = "conversation_summary",
    sync_process: bool = True,
):
    """统一记忆入口：写入 memory_events 并处理。"""
    uid = get_current_user_id()
    if uid <= 0:
        logger.warning("memory run skipped: missing current_user_id")
        return None

    source = _memory_source.get()
    svc = MemoryService()
    event_id = await svc.enqueue_event(
        user_id=uid,
        thread_id=thread_id,
        event_type=event_type,
        payload={
            "transcript": dialogue_summary,
            "source": source,
            "thread_id": thread_id,
        },
        source=source,
    )

    async def _process():
        llm = get_chat_model()
        return await svc.process_event(event_id, llm=llm)

    trace_id = get_trace_id()
    if sync_process:
        result = await _process()
        logger.info(
            "[trace=%s] memory event processed: user=%s event=%s source=%s",
            trace_id,
            uid,
            event_id,
            source,
        )
        return result

    asyncio.create_task(_process())
    logger.info(
        "[trace=%s] memory event queued: user=%s event=%s source=%s",
        trace_id,
        uid,
        event_id,
        source,
    )
    return {"event_id": event_id, "status": "queued"}
