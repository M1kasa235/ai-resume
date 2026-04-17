# app/api/v1/user.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.schemas.user import UserResponse, UserUpdate, PasswordUpdate, UserListResponse
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取个人资料"""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人资料"""
    service = UserService(db)
    updated_user = await service.update_profile(current_user, update_data)
    return updated_user

@router.put("/password")
async def change_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    service = UserService(db)
    await service.update_password(
        current_user,
        password_data.old_password,
        password_data.new_password
    )
    return {"message": "密码修改成功"}

# ==================== 管理员接口 ====================

@router.get("", response_model=UserListResponse, dependencies=[Depends(get_current_admin_user)])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表（管理员）"""
    service = UserService(db)
    total, users = await service.list_users(skip=skip, limit=limit)
    return {"total": total, "items": users}

@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_admin_user)])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取指定用户信息（管理员）"""
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user