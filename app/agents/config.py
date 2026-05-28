"""Agent 共享配置 — checkpointer 工厂 + middleware 工厂"""

import os

import aiosqlite
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agents.middleware.progress import AgentProgressMiddleware
from app.core.config import settings

CHECKPOINTER_DB_PATH = "app/db/agent_sessions/checkpoints.db"

_saver: AsyncSqliteSaver | None = None
_conn: aiosqlite.Connection | None = None


async def init_checkpointer() -> AsyncSqliteSaver:
    """创建 AsyncSqliteSaver 单例（应用启动时调用）"""
    global _saver, _conn
    if _saver is not None:
        return _saver

    os.makedirs(os.path.dirname(CHECKPOINTER_DB_PATH), exist_ok=True)
    _conn = await aiosqlite.connect(CHECKPOINTER_DB_PATH)
    _saver = AsyncSqliteSaver(_conn)
    await _saver.setup()
    return _saver


def create_checkpointer() -> AsyncSqliteSaver:
    """获取已初始化的 checkpointer（所有 agent 共享）"""
    if _saver is None:
        raise RuntimeError(
            "Agent checkpointer 未初始化，请确保应用 lifespan 已调用 init_checkpointer()"
        )
    return _saver


async def shutdown_checkpointer() -> None:
    """关闭 checkpointer 连接（应用关闭时调用）"""
    global _saver, _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
    _saver = None


def make_middleware(model, summarization_model=None, *, progress: bool = False):
    """所有 agent 统一 middleware 配置"""
    sm_model = summarization_model or model
    stack = [
        ModelRetryMiddleware(max_retries=2, initial_delay=1.0, backoff_factor=2.0, jitter=True),
        ToolCallLimitMiddleware(
            run_limit=settings.AGENT_TOOL_RUN_LIMIT,
            exit_behavior="continue",
        ),
        SummarizationMiddleware(model=sm_model, trigger=("tokens", 24000), keep=("tokens", 8000)),
    ]
    if progress:
        stack.insert(0, AgentProgressMiddleware())
    return stack
