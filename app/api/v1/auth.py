# app/api/v1/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **phone**: 手机号（可选）
    - **password**: 密码（6-20字符）
    """
    service = UserService(db)
    user = await service.create(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
        login_data: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    用户登录，返回双 Token

    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    service = UserService(db)
    user = await service.authenticate(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 生成双 Token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
        payload: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    使用 Refresh Token 获取新的 Access Token
    """
    token_payload = decode_token(payload.refresh_token)
    if not token_payload or token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    user_id = int(token_payload.get("sub"))
    service = UserService(db)
    user = await service.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )

    # 生成新的双 Token（轮换策略，可选）
    new_access = create_access_token(subject=user.id)
    new_refresh = create_refresh_token(subject=user.id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    return current_user


@router.post("/logout")
async def logout():
    """
    登出（前端清除 Token 即可，后端无状态）
    可选：将 Token 加入黑名单（使用 Redis）
    """
    return {"message": "登出成功"}
