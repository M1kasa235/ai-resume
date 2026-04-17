# app/api/v1/workbench.py
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.workbench_service import WorkbenchService
from app.schemas.workbench import ResumeInfo, ApplicationListResponse, UploadResumeResponse

router = APIRouter(prefix="/workbench", tags=["工作台"])


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(..., description="简历 PDF 文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传个人简历 PDF"""
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
