"""简历优化接口"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.job import Job
from app.rag import get_rag_service
from app.schemas.rag import (
    ResumeDiagnoseResponse,
    OptimizeRequest,
    OptimizeResponse,
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
    db: AsyncSession = Depends(get_db),
):
    """针对岗位优化简历"""
    stmt = select(Job).where(Job.id == request.job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    job_info = {
        "company_name": job.company_name,
        "title": job.title,
        "description": job.description or "",
        "requirements": job.requirements or "",
    }

    result = await get_rag_service().optimize_for_job(current_user.id, job_info)
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
