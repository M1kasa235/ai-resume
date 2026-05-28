"""RAG 接口路由"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.services.job_lookup import fetch_job
from app.api.deps import get_current_user
from app.models.user import User
from app.rag import get_rag_service
from app.schemas.rag import (
    ResumeQueryRequest,
    ResumeQueryResponse,
    JobMatchRequest,
    JobMatchResponse,
    MatchScore,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/resume/query", response_model=ResumeQueryResponse)
async def query_resume(
    request: ResumeQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """简历 RAG 问答"""
    try:
        result = await get_rag_service().query(current_user.id, request.question)
        return ResumeQueryResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG 问答失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="RAG 问答服务暂时不可用，请稍后重试。",
        )


@router.post("/job/match", response_model=JobMatchResponse)
async def match_job(
    request: JobMatchRequest,
    current_user: User = Depends(get_current_user),
):
    """岗位匹配度分析"""
    try:
        job = await fetch_job(request.job_id)
        if not job or not job.is_active:
            raise HTTPException(status_code=404, detail="岗位不存在")

        data = await get_rag_service().match_job(current_user.id, job)
        return JobMatchResponse(
            overall_score=data["overall_score"],
            scores=[MatchScore(**s) for s in data["scores"]],
            analysis=data["analysis"],
            suggestions=data["suggestions"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"岗位匹配失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="岗位匹配服务暂时不可用，请稍后重试。",
        )
