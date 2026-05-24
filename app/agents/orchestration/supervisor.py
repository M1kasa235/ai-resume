"""Supervisor agent factory and streaming entrypoint."""

import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage

from app.agents.config import create_checkpointer, make_middleware
from app.agents.context.assembler import assemble_context
from app.agents.memory import MemoryService
from app.agents.orchestration.prompt import SUPERVISOR_PROMPT
from app.agents.orchestration.tools import SUPERVISOR_TOOLS
from app.agents.orchestration.triggers import maybe_trigger_memory_agent
from app.agents.registry import AgentRegistry
from app.agents.trace import AgentTrace
from app.core.async_tasks import create_context_task
from app.core.context import get_trace_id, require_current_user_id, update_request_context
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)


def get_supervisor():
    """懒加载 supervisor agent"""

    def _build():
        model = get_chat_model()
        return create_agent(
            model=model,
            tools=SUPERVISOR_TOOLS,
            system_prompt=SUPERVISOR_PROMPT,
            checkpointer=create_checkpointer(),
            middleware=make_middleware(model),
            name="supervisor",
        )

    return AgentRegistry.get_or_create("supervisor", _build)


async def supervisor_stream(prompt: str, thread_id: str):
    """流式调用 supervisor agent"""
    update_request_context(thread_id=thread_id)
    uid = require_current_user_id()
    tid = get_trace_id()
    logger.info("[trace=%s] supervisor_stream start user=%s prompt=%s", tid, uid, prompt[:80])

    try:
        bundle = await assemble_context(uid, thread_id, prompt)
        enriched = bundle.render()
        logger.info("[trace=%s] context_bundle %s", tid, bundle.to_log_dict())
    except Exception:
        logger.warning("context assembly failed, falling back to memory-only", exc_info=True)
        memory_ctx = await MemoryService().format_context(uid, query=prompt)
        enriched = f"{memory_ctx}\n\n{prompt}" if memory_ctx else prompt

    create_context_task(maybe_trigger_memory_agent(thread_id))

    message = HumanMessage(content=enriched)
    try:
        agent = get_supervisor()
        async with AgentTrace("supervisor"):
            async for chunk, metadata in agent.astream(
                {"messages": [message]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield chunk.content
    except Exception as e:
        logger.error("[trace=%s] Supervisor 流式调用失败: %s", get_trace_id(), e)
        yield f"处理失败：{str(e)}"
