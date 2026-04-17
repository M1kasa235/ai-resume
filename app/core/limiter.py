# app/core/limiter.py
"""请求频率限制配置"""
import time
from typing import Dict
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 简单的内存限流器（生产环境建议使用 Redis）
class SimpleRateLimiter:
    """基于IP的简单限流器"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.default_limit = 200  # 默认每分钟200次
        self.window = 60  # 时间窗口（秒）
    
    def is_allowed(self, client_ip: str, limit: int = None) -> bool:
        """检查请求是否允许"""
        if limit is None:
            limit = self.default_limit
        
        now = time.time()
        # 清理过期记录
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        # 检查是否超限
        if len(self.requests[client_ip]) >= limit:
            return False
        
        # 记录本次请求
        self.requests[client_ip].append(now)
        return True


# 创建全局限流器实例
rate_limiter = SimpleRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        
        # 针对不同路径设置不同限流
        limit = rate_limiter.default_limit
        if "/auth/login" in path or "/auth/register" in path:
            limit = 5  # 认证接口更严格
        
        if not rate_limiter.is_allowed(client_ip, limit):
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "detail": "请求过于频繁，请稍后再试"
                }
            )
        
        response = await call_next(request)
        return response
