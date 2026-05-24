"""统一 Agent 聊天入口 — Supervisor 编排多智能体"""

import logging
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user, inject_request_context
from app.models.user import User
from app.agents.supervisor import supervisor_stream
from app.agents.agent import get_chat_history, clear_chat_history
from app.core.request_context import RequestContext, update_request_context
from app.core.async_tasks import create_context_task

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
    _ctx: RequestContext = Depends(inject_request_context),
):
    """统一聊天入口，Supervisor 编排子 agent 处理"""
    isolated_thread_id = f"user_{current_user.id}_{request.thread_id}"
    update_request_context(thread_id=isolated_thread_id)
    return StreamingResponse(
        supervisor_stream(request.message, isolated_thread_id),
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
    _ctx: RequestContext = Depends(inject_request_context),
):
    """清空会话历史"""
    isolated_thread_id = f"user_{current_user.id}_{thread_id}"
    update_request_context(thread_id=isolated_thread_id)

    from app.agents.config import create_checkpointer
    from app.agents.context.threads import list_related_threads
    from app.agents.memory.ingest import run_memory_agent, set_memory_source
    from app.agents.orchestration.triggers import reset_round_counters

    checkpoint = create_checkpointer().get({"configurable": {"thread_id": isolated_thread_id}})
    summary = ""
    if checkpoint and checkpoint.get("channel_values"):
        messages = checkpoint["channel_values"].get("messages", [])
        recent = [m.content for m in messages if hasattr(m, "content") and m.content]
        summary = "\n".join(recent[-20:])

    clear_chat_history(isolated_thread_id)

    checkpointer = create_checkpointer()
    related_threads = list_related_threads(isolated_thread_id, current_user.id)
    for tid in related_threads:
        try:
            checkpointer.delete_thread(tid)
        except Exception:
            logger.debug("清理子线程失败: %s", tid, exc_info=True)

    reset_round_counters(isolated_thread_id, *related_threads)

    if summary:
        set_memory_source("thread_clear")
        create_context_task(
            run_memory_agent(
                summary,
                thread_id=f"{isolated_thread_id}_clear",
                event_type="thread_clear",
                sync_process=False,
            )
        )
    return {"success": True}
