"""Sub-agent invocation with timeout and structured passthrough."""

import asyncio
import logging
from datetime import date

from langchain_core.messages import HumanMessage

from app.agents.agent import get_career_agent
from app.agents.context.threads import build_sub_agent_thread
from app.agents.orchestration.constants import (
    PASSTHROUGH_END,
    PASSTHROUGH_START,
    SUB_AGENT_TIMEOUT,
    is_structured_query,
)
from app.agents.resume_agent import get_resume_agent
from app.agents.tools.resume_formatters import strip_json_from_reply
from app.agents.trace import AgentTrace
from app.core.context import get_conversation_thread_id

logger = logging.getLogger(__name__)


async def invoke_sub_agent(role: str, query: str, uid: int) -> str:
    """调用单个子 agent，返回回复文本。超时返回友好提示。"""
    agent = get_resume_agent() if role == "resume" else get_career_agent()
    parent_thread_id = get_conversation_thread_id()
    thread_id = build_sub_agent_thread(parent_thread_id, role, uid)
    today = date.today().isoformat()
    contextualized = f"[系统上下文：今天是 {today}]\n\n{query}"
    try:
        async with AgentTrace(f"{role}_agent"):
            result = await asyncio.wait_for(
                agent.ainvoke(
                    {"messages": [HumanMessage(content=contextualized)]},
                    {"configurable": {"thread_id": thread_id}},
                ),
                timeout=SUB_AGENT_TIMEOUT,
            )
        reply = result["messages"][-1].content
        if role == "resume":
            reply = strip_json_from_reply(reply)
            if is_structured_query(query):
                reply = f"{PASSTHROUGH_START}\n{reply}\n{PASSTHROUGH_END}"
        return reply
    except asyncio.TimeoutError:
        logger.error("%s_agent 超时 (%ss)", role, SUB_AGENT_TIMEOUT)
        return f"[{role} 专家响应超时，请稍后重试或简化你的问题]"
    except Exception as e:
        logger.error("%s_agent 调用失败: %s", role, e)
        return f"[{role} 专家暂时不可用] {str(e)}"
