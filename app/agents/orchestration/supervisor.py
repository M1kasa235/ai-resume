"""Supervisor streaming entrypoint."""

from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.context.assembler import assemble_context
from app.agents.factories.supervisor import get_supervisor
from app.agents.memory import MemoryService
from app.agents.orchestration.constants import should_bypass_supervisor_for_resume
from app.agents.common.errors import agent_stream_error_message
from app.agents.common.run_config import agent_run_config
from app.agents.common.progress import (
    STATUS_ASSEMBLE_CONTEXT,
    STATUS_COORDINATE,
    STATUS_RESUME_DIAGNOSE,
    STATUS_UNDERSTAND,
)
from app.agents.common.streaming import (
    extract_custom_event,
    extract_stream_text,
    iter_text_chunks,
    sse_event,
)
from app.agents.orchestration.sub_agent import invoke_sub_agent
from app.agents.orchestration.triggers import maybe_trigger_memory_agent
from app.agents.prompts.shared import web_search_preference_block
from app.agents.session.checkpoint import append_thread_messages, replace_last_human_message
from app.agents.tools.resume_formatters import extract_passthrough, normalize_structured_reply
from app.agents.trace import AgentTrace
from app.core.async_tasks import create_context_task
from app.core.context import get_trace_id, require_current_user_id, update_request_context

logger = logging.getLogger(__name__)


async def _stream_bypass_resume(prompt: str, thread_id: str, uid: int):
    yield sse_event("status", message=STATUS_RESUME_DIAGNOSE, step="resume_diagnose")

    raw = await invoke_sub_agent("resume", prompt, uid)

    body = normalize_structured_reply(extract_passthrough(raw) or raw)
    await append_thread_messages(
        get_supervisor(),
        thread_id,
        [HumanMessage(content=prompt), AIMessage(content=body)],
    )

    for piece in iter_text_chunks(body):
        yield sse_event("token", content=piece)
    yield sse_event("done")


async def _stream_supervisor_agent(
    prompt: str,
    thread_id: str,
    enriched: str,
):
    agent = get_supervisor()
    config = agent_run_config(thread_id)

    async with AgentTrace("supervisor"):
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=enriched)]},
            config,
            version="v2",
        ):
            custom = extract_custom_event(event)
            if custom:
                yield sse_event("status", message=custom["message"], step=custom["step"])
                continue

            if event.get("event") == "on_chat_model_stream":
                text = extract_stream_text(event.get("data", {}).get("chunk"))
                if text:
                    yield sse_event("token", content=text)

    try:
        await replace_last_human_message(agent, thread_id, prompt)
    except Exception:
        logger.warning("failed to store plain user message", exc_info=True)


async def supervisor_stream(
    prompt: str,
    thread_id: str,
    web_search_enabled: bool = False,
):
    """流式调用 supervisor agent，输出 SSE：status / token / done。"""
    update_request_context(thread_id=thread_id, web_search_enabled=web_search_enabled)
    uid = require_current_user_id()
    tid = get_trace_id()
    logger.info(
        "[trace=%s] supervisor_stream start user=%s web_search=%s prompt=%s",
        tid,
        uid,
        web_search_enabled,
        prompt[:80],
    )

    create_context_task(maybe_trigger_memory_agent(thread_id))

    yield sse_event("status", message=STATUS_UNDERSTAND, step="understand")

    if should_bypass_supervisor_for_resume(prompt):
        logger.info("[trace=%s] resume passthrough bypass user=%s", tid, uid)
        try:
            async for line in _stream_bypass_resume(prompt, thread_id, uid):
                yield line
            return
        except Exception:
            logger.warning(
                "[trace=%s] resume passthrough bypass failed, falling back to supervisor",
                tid,
                exc_info=True,
            )

    try:
        yield sse_event("status", message=STATUS_ASSEMBLE_CONTEXT, step="context")
        bundle = await assemble_context(uid, thread_id, prompt)
        enriched = bundle.render()
        logger.info("[trace=%s] context_bundle %s", tid, bundle.to_log_dict())
    except Exception:
        logger.warning("context assembly failed, falling back to memory-only", exc_info=True)
        memory_ctx = await MemoryService().format_context(uid, query=prompt)
        enriched = f"{memory_ctx}\n\n{prompt}" if memory_ctx else prompt

    enriched = f"{web_search_preference_block(web_search_enabled)}\n\n{enriched}"
    yield sse_event("status", message=STATUS_COORDINATE, step="coordinate")

    try:
        async for line in _stream_supervisor_agent(prompt, thread_id, enriched):
            yield line
        yield sse_event("done")
    except Exception as e:
        logger.error("[trace=%s] Supervisor 流式调用失败: %s", get_trace_id(), e, exc_info=True)
        yield sse_event("token", content=agent_stream_error_message(e))
        yield sse_event("done")
