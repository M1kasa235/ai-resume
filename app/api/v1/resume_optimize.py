"""简历优化接口"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.job_lookup import fetch_job, job_info_from_model
from app.api.deps import get_current_user
from app.models.user import User
from app.rag import get_rag_service
from app.schemas.rag import (
    OptimizeRequest,
    OptimizeResponse,
    ResumeDiagnoseResponse,
)

router = APIRouter(prefix="/resume", tags=["简历优化"])


@router.post("/diagnose", response_model=ResumeDiagnoseResponse)
async def diagnose_resume(current_user: User = Depends(get_current_user)):
    """简历诊断"""
    result = await get_rag_service().diagnose(current_user.id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResumeDiagnoseResponse(**result)


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    """针对岗位优化简历"""
    job = await fetch_job(request.job_id)
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="岗位不存在")

    result = await get_rag_service().optimize_for_job(
        current_user.id,
        job_info_from_model(job),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return OptimizeResponse(**result)


class PolishRequest(BaseModel):
    section: str
    content: str


@router.post("/polish")
async def polish_section(
    request: PolishRequest,
    current_user: User = Depends(get_current_user),
):
    """单段润色"""
    result = await get_rag_service().polish(request.section, request.content)
    return result
