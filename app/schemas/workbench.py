from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ResumeInfo(BaseModel):
    """简历信息响应模型"""
    model_config = ConfigDict(from_attributes=True)

    resume_url: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None


class ApplicationItem(BaseModel):
    """投递记录单项模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    job_title: str
    status: Optional[str] = None
    applied_at: Optional[datetime] = None
    created_at: datetime


class ApplicationListResponse(BaseModel):
    """投递记录列表响应模型"""
    total: int
    page: int
    size: int
    items: List[ApplicationItem]


class UploadResumeResponse(BaseModel):
    """上传简历响应模型"""
    url: str
    message: str
