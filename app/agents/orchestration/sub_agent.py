"""Sub-agent invocation with timeout and structured passthrough."""

import asyncio
import logging

from langchain_core.messages import HumanMessage

from app.agents.common.protocol import PASSTHROUGH_END, PASSTHROUGH_START, SUB_AGENT_TIMEOUT
from app.agents.common.run_config import agent_run_config
from app.agents.context.temporal import user_message_with_date
from app.agents.context.threads import build_ephemeral_sub_agent_thread, build_sub_agent_thread
from app.agents.orchestration.constants import is_structured_query
from app.agents.registry import AgentRegistry
from app.agents.tools.resume_formatters import normalize_structured_reply
from app.agents.trace import AgentTrace
from app.core.context import get_conversation_thread_id

logger = logging.getLogger(__name__)


async def invoke_sub_agent(role: str, query: str, uid: int) -> str:
    """调用单个子 agent，返回回复文本。超时返回友好提示。"""
    try:
        agent = AgentRegistry.get_agent_for_role(role)
    except ValueError:
        logger.error("unknown sub-agent role: %s", role)
        return f"[未知专家角色: {role}]"

    parent_thread_id = get_conversation_thread_id()
    structured = role == "resume" and is_structured_query(query)
    if structured:
        thread_id = build_ephemeral_sub_agent_thread(parent_thread_id, role, uid)
    else:
        thread_id = build_sub_agent_thread(parent_thread_id, role, uid)
    contextualized = user_message_with_date(query)
    try:
        async with AgentTrace(f"{role}_agent"):
            result = await asyncio.wait_for(
                agent.ainvoke(
                    {"messages": [HumanMessage(content=contextualized)]},
                    agent_run_config(thread_id),
                ),
                timeout=SUB_AGENT_TIMEOUT,
            )
        reply = result["messages"][-1].content
        if role == "resume":
            reply = normalize_structured_reply(reply)
            if structured:
                reply = f"{PASSTHROUGH_START}\n{reply}\n{PASSTHROUGH_END}"
        return reply
    except asyncio.TimeoutError:
        logger.error("%s_agent 超时 (%ss)", role, SUB_AGENT_TIMEOUT)
        return f"[{role} 专家响应超时，请稍后重试或简化你的问题]"
    except Exception as e:
        logger.error("%s_agent 调用失败: %s", role, e)
        return f"[{role} 专家暂时不可用] {str(e)}"
