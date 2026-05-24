"""统一 Agent 聊天入口 — Supervisor 编排多智能体"""

import logging
import asyncio
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user
from app.models.user import User
from app.agents.supervisor import supervisor_stream
from app.agents.agent import get_chat_history, clear_chat_history
from app.core.context import set_current_user_id, set_trace_id, get_trace_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["智能对话"])


class UnifiedChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    image_url: Optional[str] = None


@router.post("/agent/chat/stream")
async def unified_chat(
    request: UnifiedChatRequest,
    current_user: User = Depends(get_current_user),
):
    """统一聊天入口，Supervisor 编排子 agent 处理"""
    from datetime import date
    set_current_user_id(current_user.id)
    trace_id = set_trace_id()
    isolated_thread_id = f"user_{current_user.id}_{request.thread_id}"
    today = date.today().isoformat()
    enriched = f"[今天是 {today}]\n{request.message}"
    return StreamingResponse(
        supervisor_stream(enriched, isolated_thread_id),
        media_type="text/event-stream",
    )


@router.get("/agent/chat/history")
async def get_history(
    thread_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
):
    """获取会话历史消息"""
    isolated_thread_id = f"user_{current_user.id}_{thread_id}"
    messages = get_chat_history(isolated_thread_id)
    return {"messages": messages}


@router.delete("/agent/chat/history")
async def clear_history(
    thread_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
):
    """清空会话历史"""
    set_current_user_id(current_user.id)
    isolated_thread_id = f"user_{current_user.id}_{thread_id}"

    # 在 delete 前捕获对话摘要，避免竞态
    from app.agents.config import create_checkpointer
    from app.agents.memory_agent import run_memory_agent
    checkpoint = create_checkpointer().get({"configurable": {"thread_id": isolated_thread_id}})
    summary = ""
    if checkpoint and checkpoint.get("channel_values"):
        messages = checkpoint["channel_values"].get("messages", [])
        recent = [m.content for m in messages if hasattr(m, "content") and m.content]
        summary = "\n".join(recent[-20:])

    clear_chat_history(isolated_thread_id)

    # 同时清理关联的子 agent / 记忆线程，确保“清空会话”语义一致。
    checkpointer = create_checkpointer()
    related_threads = [
        f"{isolated_thread_id}:resume",
        f"{isolated_thread_id}:career",
        f"{isolated_thread_id}:memory",
        f"{isolated_thread_id}_auto",
        f"{isolated_thread_id}_clear",
        # 兼容历史 thread 规则（user_{uid}_{role}）。
        f"user_{current_user.id}_resume",
        f"user_{current_user.id}_career",
        f"user_{current_user.id}_memory",
    ]
    for tid in related_threads:
        try:
            checkpointer.delete_thread(tid)
        except Exception:
            logger.debug("清理子线程失败: %s", tid, exc_info=True)

    # 清理轮数计数器
    from app.agents.supervisor import _message_counter
    _message_counter.pop(isolated_thread_id, None)
    for tid in related_threads:
        _message_counter.pop(tid, None)

    if summary:
        from app.agents.memory_agent import set_memory_source
        set_memory_source("thread_clear")
        asyncio.create_task(run_memory_agent(summary, f"{isolated_thread_id}_clear"))
    return {"success": True}
