"""Agent 共享配置 — checkpointer 工厂 + middleware 工厂"""

import threading
import asyncio
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    ToolCallLimitMiddleware,
    SummarizationMiddleware,
)

CHECKPOINTER_DB_PATH = "app/db/agent_sessions/checkpoints.db"

_saver = None
_loop = None


def _ensure_loop():
    """启动并缓存一个持久的 event loop（daemon 线程），
    AsyncSqliteSaver 后续所有异步操作都依赖此 loop。"""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        t = threading.Thread(target=_loop.run_forever, daemon=True)
        t.start()
    return _loop


def create_checkpointer() -> AsyncSqliteSaver:
    """创建 AsyncSqliteSaver 单例（所有 agent 共享）

    在持久 daemon 线程中完成异步初始化，loop 保持运行以确保
    get/put/astream 等后续操作可用。"""
    global _saver
    if _saver is not None:
        return _saver

    loop = _ensure_loop()

    async def _init():
        conn = await aiosqlite.connect(CHECKPOINTER_DB_PATH)
        saver = AsyncSqliteSaver(conn)
        await saver.setup()
        return saver

    future = asyncio.run_coroutine_threadsafe(_init(), loop)
    _saver = future.result(timeout=15)
    return _saver


def make_middleware(model, summarization_model=None):
    """所有 agent 统一 middleware 配置"""
    sm_model = summarization_model or model
    return [
        ModelRetryMiddleware(max_retries=2, initial_delay=1.0, backoff_factor=2.0, jitter=True),
        ToolCallLimitMiddleware(run_limit=30, exit_behavior="continue"),
        SummarizationMiddleware(model=sm_model, trigger=("tokens", 24000), keep=("tokens", 8000)),
    ]
