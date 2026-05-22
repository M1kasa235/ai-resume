# app/api/v1/workbench.py
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.job import Job
from app.services.workbench_service import WorkbenchService
from app.schemas.workbench import ResumeInfo, ApplicationListResponse, UploadResumeResponse, ApplicationCreate, ApplicationResponse

router = APIRouter(prefix="/workbench", tags=["工作台"])


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(..., description="简历文件（PDF 或 TXT）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传个人简历（支持 PDF 和 TXT 格式）"""
    service = WorkbenchService(db)
    return await service.upload_resume(current_user.id, file)


@router.get("/resume", response_model=ResumeInfo)
async def get_resume_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的简历信息及基础画像"""
    service = WorkbenchService(db)
    return await service.get_resume_info(current_user.id)


@router.get("/applications", response_model=ApplicationListResponse)
async def get_applications(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """分页获取个人的投递记录"""
    service = WorkbenchService(db)
    return await service.get_applications(current_user.id, page, size)


@router.post("/applications", response_model=ApplicationResponse, status_code=201)
async def apply_job(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """投递简历到指定岗位"""
    from app.models.application import Application
    
    # 检查岗位是否存在
    job = await db.get(Job, application_data.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    # 检查是否已经投递过
    from sqlalchemy import select
    stmt = select(Application).where(
        Application.user_id == current_user.id,
        Application.job_id == application_data.job_id
    )
    result = await db.execute(stmt)
    existing_application = result.scalar_one_or_none()
    
    if existing_application:
        raise HTTPException(status_code=400, detail="您已经投递过该岗位")
    
    # 创建投递记录
    new_application = Application(
        user_id=current_user.id,
        job_id=application_data.job_id,
        company_name=job.company_name,
        job_title=job.title,
        status='applied',
        applied_at=datetime.utcnow(),
        notes=application_data.notes
    )
    
    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)
    
    return new_application
