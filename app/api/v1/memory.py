"""长期记忆调试与运维端点（事件化 memory pipeline）。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User
from app.core.llm import get_chat_model
from app.core.context import set_current_user_id
from app.agents.memory import MemoryService

router = APIRouter(prefix="/memory", tags=["长期记忆"])


class ExtractRequest(BaseModel):
    transcript: str = Field(..., description="对话文本或摘要")
    source: str = Field(default="manual", description="来源标记")
    thread_id: str = Field(default="manual", description="逻辑线程标识")
    event_type: str = Field(default="manual_extract", description="事件类型")
    process_now: bool = Field(default=True, description="是否立即处理事件")


class RetryRequest(BaseModel):
    reset_retry_count: bool = Field(default=True, description="是否重置重试计数")
    process_now: bool = Field(default=True, description="是否立即处理")


class RetryDeadLetterRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    process_now: bool = Field(default=False)


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
    """手动触发记忆提取（统一走事件队列）。"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    llm = get_chat_model()
    event_id = await svc.enqueue_event(
        user_id=current_user.id,
        thread_id=f"user_{current_user.id}_{body.thread_id}",
        event_type=body.event_type,
        payload={"transcript": body.transcript, "source": body.source},
        source=body.source,
    )

    if not body.process_now:
        return {"status": "queued", "event_id": event_id}

    result = await svc.process_event(event_id, llm=llm)
    status = "done" if result and result.get("delta") else "no_change"
    return {"status": status, "event_id": event_id, "result": result}


@router.get("/events")
async def list_memory_events(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """查看当前用户记忆事件（支持按状态筛选）。"""
    svc = MemoryService()
    items = await svc.list_events(
        user_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "total": len(items),
        "items": items,
        "status_filter": status,
        "limit": limit,
        "offset": offset,
    }


@router.get("/events/dead-letter")
async def list_dead_letter_events(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """查看当前用户死信事件。"""
    svc = MemoryService()
    items = await svc.list_events(
        user_id=current_user.id,
        status="dead_letter",
        limit=limit,
        offset=offset,
    )
    return {
        "total": len(items),
        "items": items,
        "limit": limit,
        "offset": offset,
    }


@router.get("/events/stats")
async def memory_event_stats(current_user: User = Depends(get_current_user)):
    """记忆事件统计（含 pending/failed/dead_letter）。"""
    svc = MemoryService()
    stats = await svc.get_event_stats(current_user.id)
    return stats


@router.post("/events/{event_id}/retry")
async def retry_memory_event(
    event_id: str,
    body: RetryRequest,
    current_user: User = Depends(get_current_user),
):
    """重试一条事件（支持立即处理）。"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    event = await svc.retry_event(
        event_id=event_id,
        user_id=current_user.id,
        reset_retry_count=body.reset_retry_count,
    )
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    if not body.process_now:
        return {"status": "requeued", "event": event}

    llm = get_chat_model()
    result = await svc.process_event(event_id, llm=llm)
    return {"status": "processed", "event_id": event_id, "result": result}


@router.post("/events/retry-dead-letter")
async def retry_dead_letter_events(
    body: RetryDeadLetterRequest,
    current_user: User = Depends(get_current_user),
):
    """批量重试当前用户 dead_letter 事件。"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    requeued = await svc.retry_dead_letter_events(current_user.id, limit=body.limit)

    processed = 0
    if body.process_now and requeued > 0:
        llm = get_chat_model()
        processed = await svc.process_pending_events(llm=llm, batch_size=requeued, user_id=current_user.id)

    return {
        "status": "done",
        "requeued": requeued,
        "processed": processed,
    }


@router.post("/events/process-pending")
async def process_pending_memory_events(
    batch_size: int = Query(default=20, ge=1, le=200),
    max_retries: int = Query(default=3, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    """手动触发一次 pending/failed 事件消费。"""
    set_current_user_id(current_user.id)
    svc = MemoryService()
    llm = get_chat_model()
    processed = await svc.process_pending_events(
        llm=llm,
        batch_size=batch_size,
        max_retries=max_retries,
        user_id=current_user.id,
    )
    return {
        "status": "done",
        "processed": processed,
        "batch_size": batch_size,
        "max_retries": max_retries,
    }


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
