# app/schemas/user.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==================== 基础模型 ====================

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$', description="手机号")


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(..., min_length=6, max_length=20, description="密码")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
            "password": "123456"
        }
    })


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """用户信息更新请求（可选字段）"""
    real_name: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, pattern=r'^(male|female|other)$')
    current_city: Optional[str] = None
    target_city: Optional[str] = None
    work_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordUpdate(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


# ==================== 响应模型 ====================

class UserResponse(UserBase):
    """用户详情响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: Optional[str] = None
    resume_url: Optional[str] = None
    real_name: Optional[str] = None
    gender: Optional[str] = None
    current_city: Optional[str] = None
    target_city: Optional[str] = None
    work_years: Optional[int] = None
    education: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """用户列表响应（管理员用，脱敏）"""
    total: int
    items: List[UserResponse]