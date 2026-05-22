"""AgentTrace — 结构化 Agent 调用追踪，不侵入业务逻辑"""

import time
import logging
from app.core.context import get_trace_id

logger = logging.getLogger(__name__)


class AgentTrace:
    """Agent 调用追踪，用法:

        async with AgentTrace("career_agent"):
            result = await agent.ainvoke(...)

    自动输出 start / duration / status 日志。
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.t0 = None

    async def __aenter__(self):
        self.t0 = time.time()
        tid = get_trace_id()
        logger.info(f"[trace={tid}] agent={self.agent_name} start")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = int((time.time() - self.t0) * 1000)
        tid = get_trace_id()
        status = "fail" if exc_type else "ok"
        logger.info(
            f"[trace={tid}] agent={self.agent_name} duration={elapsed}ms status={status}"
        )
        return False  # 不吞异常
