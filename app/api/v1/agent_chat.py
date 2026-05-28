"""统一 Agent 聊天入口 — Supervisor 编排多智能体"""

import logging
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user, inject_request_context
from app.models.user import User
from app.agents.facade.chat import (
    clear_conversation_with_memory,
    get_chat_history,
    supervisor_stream,
)
from app.core.request_context import RequestContext, update_request_context

logger = logging.getLogger(__name__)
router = APIRouter(tags=["智能对话"])


class UnifiedChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    image_url: Optional[str] = None
    web_search_enabled: bool = False


@router.post("/agent/chat/stream")
async def unified_chat(
    request: UnifiedChatRequest,
    current_user: User = Depends(get_current_user),
    _ctx: RequestContext = Depends(inject_request_context),
):
    """统一聊天入口，Supervisor 编排子 agent 处理"""
    isolated_thread_id = f"user_{current_user.id}_{request.thread_id}"
    update_request_context(
        thread_id=isolated_thread_id,
        web_search_enabled=request.web_search_enabled,
    )
    logger.info(
        "chat stream user=%s thread=%s web_search=%s",
        current_user.id,
        isolated_thread_id,
        request.web_search_enabled,
    )
    return StreamingResponse(
        supervisor_stream(
            request.message,
            isolated_thread_id,
            web_search_enabled=request.web_search_enabled,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agent/chat/history")
async def get_history(
    thread_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
):
    """获取会话历史消息"""
    isolated_thread_id = f"user_{current_user.id}_{thread_id}"
    messages = await get_chat_history(isolated_thread_id)
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
    await clear_conversation_with_memory(isolated_thread_id, current_user.id)
    return {"success": True}
