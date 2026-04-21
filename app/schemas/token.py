# app/schemas/token.py
from pydantic import BaseModel

class Token(BaseModel):
    """登录成功返回的Token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access_token 有效期（秒）

class TokenPayload(BaseModel):
    """JWT Token 载荷"""
    sub: str  # 用户ID
    exp: int    # 过期时间戳
    type: str   # token类型：access/refresh


class RefreshTokenRequest(BaseModel):
    """刷新Token请求体"""
    refresh_token: str