# app/schemas/common.py
"""通用响应模型"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[T] = Field(..., description="数据列表")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    
    @property
    def total_pages(self) -> int:
        """计算总页数"""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class SuccessResponse(BaseModel):
    """成功响应模型"""
    message: str = Field("操作成功", description="提示信息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error_code: str = Field(..., description="错误代码")
    detail: str = Field(..., description="错误详情")
    data: Optional[dict] = Field(None, description="额外数据")
