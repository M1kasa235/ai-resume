# app/api/deps.py
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User
from app.schemas.token import TokenPayload

# 配置日志
logger = logging.getLogger(__name__)

# 安全方案 - auto_error=True 让 Swagger UI 正确显示和使用认证
security = HTTPBearer(auto_error=True)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    从 Authorization: Bearer <token> 中提取并验证
    """
    token = credentials.credentials
    logger.debug(f"收到 Token: {token[:20]}...")  # 只记录前20个字符
    
    payload = decode_token(token)
    logger.debug(f"Token 解码结果: {'成功' if payload else '失败'}")

    if not payload or payload.get("type") != "access":
        logger.warning(f"Token 验证失败: type={payload.get('type') if payload else None}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))
    if not user_id:
        logger.warning("Token 中 user_id 为空")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭证",
        )

    logger.debug(f"查询用户 ID: {user_id}")
    # 查询用户
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"用户 {user_id} 不存在")
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.is_active:
        logger.warning(f"用户 {user_id} 已被禁用")
        raise HTTPException(status_code=400, detail="用户已被禁用")

    logger.debug(f"认证成功: {user.username}")
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """确保用户已登录且处于激活状态"""
    return current_user


async def get_current_admin_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """确保用户是管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user