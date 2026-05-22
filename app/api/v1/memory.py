"""长期记忆调试端点"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User
from app.core.llm import get_chat_model
from app.core.context import set_current_user_id
from app.agents.memory import MemoryService

router = APIRouter()


class ExtractRequest(BaseModel):
    transcript: str = Field(..., description="对话文本或摘要")
    source: str = Field(default="manual", description="来源标记")


class ConsolidateRequest(BaseModel):
    pass


@router.get("/list")
async def list_memories(current_user: User = Depends(get_current_user)):
    """查看当前用户的所有长期记忆"""
    svc = MemoryService()
    memories = await svc.get_all(current_user.id)
    return {
        "total": len(memories),
        "items": memories,
    }


@router.post("/extract")
async def extract_memories(
    body: ExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """手动触发记忆提取"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    llm = get_chat_model()
    delta = await svc.extract_from_transcript(
        current_user.id, body.transcript, body.source, llm,
    )
    if delta:
        MemoryService.invalidate_cache(current_user.id)
    return {"status": "done" if delta else "no_change", "delta": delta}


@router.delete("/{category}/{mem_key}")
async def delete_memory(
    category: str,
    mem_key: str,
    current_user: User = Depends(get_current_user),
):
    """删除单条记忆"""
    svc = MemoryService()
    await svc.delete(current_user.id, category, mem_key)
    MemoryService.invalidate_cache(current_user.id)
    return {"status": "deleted"}


@router.post("/consolidate")
async def consolidate_memories(
    current_user: User = Depends(get_current_user),
):
    """手动触发记忆整合（合并同类项）"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    llm = get_chat_model()
    await svc.consolidate(current_user.id, llm)
    MemoryService.invalidate_cache(current_user.id)
    count = await svc.count(current_user.id)
    return {"status": "done", "count": count}
