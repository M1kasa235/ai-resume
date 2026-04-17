# app/core/exceptions.py
"""自定义异常类"""
from typing import Optional, Any
from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常类"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "服务器内部错误",
        error_code: Optional[str] = None,
        data: Optional[Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.data = data


class AuthenticationError(AppException):
    """认证错误"""
    
    def __init__(self, detail: str = "认证失败，请重新登录"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTH_ERROR"
        )


class PermissionDenied(AppException):
    """权限不足"""
    
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED"
        )


class NotFoundError(AppException):
    """资源不存在"""
    
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class ValidationError(AppException):
    """数据验证错误"""
    
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )


class BusinessError(AppException):
    """业务逻辑错误"""
    
    def __init__(self, detail: str = "业务处理失败", error_code: str = "BUSINESS_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class DuplicateError(BusinessError):
    """重复操作错误"""
    
    def __init__(self, detail: str = "记录已存在"):
        super().__init__(detail=detail, error_code="DUPLICATE_ERROR")
