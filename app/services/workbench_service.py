# app/services/workbench_service.py
import os
import uuid
import shutil
from typing import Dict, List
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.user import User
from app.models.application import Application
from app.schemas.workbench import ResumeInfo, ApplicationListResponse, ApplicationItem


class WorkbenchService:
    """工作台业务逻辑服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = "uploads/resumes"

    async def upload_resume(self, user_id: int, file: UploadFile) -> Dict[str, str]:
        """
        上传简历 PDF
        """
        # 1. 验证文件类型
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="只支持 PDF 格式的简历")
        
        # 2. 验证文件大小 (限制为 10MB)
        file.file.seek(0, 2)  # 移动到文件末尾
        size = file.file.tell()
        file.file.seek(0)  # 移回开头
        if size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

        # 3. 生成唯一文件名并保存
        ext = "pdf"
        filename = f"{uuid.uuid4()}.{ext}"
        user_dir = os.path.join(self.upload_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

        # 4. 更新数据库中的简历路径
        resume_url = f"/uploads/resumes/{user_id}/{filename}"
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.avatar_url = resume_url  # 暂时复用 avatar_url 字段存储简历路径
            await self.db.commit()
            await self.db.refresh(user)

        return {"url": resume_url, "message": "上传成功"}

    async def get_resume_info(self, user_id: int) -> ResumeInfo:
        """获取当前用户的简历信息"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
            
        return ResumeInfo(
            resume_url=user.avatar_url,
            real_name=user.real_name,
            phone=user.phone,
            email=user.email,
            education=user.education
        )

    async def get_applications(self, user_id: int, page: int = 1, size: int = 10) -> ApplicationListResponse:
        """获取投递记录列表"""
        offset = (page - 1) * size
        
        # 查询总数
        count_stmt = select(func.count()).select_from(Application).where(Application.user_id == user_id)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        stmt = select(Application).where(
            Application.user_id == user_id
        ).order_by(
            desc(Application.created_at)
        ).offset(offset).limit(size)
        
        result = await self.db.execute(stmt)
        applications = result.scalars().all()

        items = [
            ApplicationItem(
                id=app.id,
                company_name=app.company_name,
                job_title=app.job_title,
                status=app.status,
                applied_at=app.applied_at,
                created_at=app.created_at
            ) for app in applications
        ]

        return ApplicationListResponse(
            total=total,
            page=page,
            page_size=size,
            items=items
        )
