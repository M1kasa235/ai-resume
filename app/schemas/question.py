# app/schemas/question.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 题目分类 ====================

class QuestionCategoryBase(BaseModel):
    """分类基础字段"""
    name: str = Field(..., max_length=50, description="分类名称")
    type: str = Field(..., description="题目类型: tech/algorithm/behavior/hr")
    parent_id: Optional[int] = Field(None, description="父分类ID")


class QuestionCategoryResponse(QuestionCategoryBase):
    """分类响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sort_order: int
    is_active: bool
    created_at: datetime


class QuestionCategoryTree(QuestionCategoryResponse):
    """分类树结构"""
    children: List["QuestionCategoryTree"] = []


# ==================== 题目相关 ====================

class QuestionListItem(BaseModel):
    """题目列表项（精简版）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    type: str
    difficulty: Optional[str] = None
    tags: Optional[list] = None
    frequency: int = 0
    is_hot: bool = False


class QuestionDetail(BaseModel):
    """题目详情"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category_id: int
    title: str
    content: Optional[str] = None
    type: str
    difficulty: Optional[str] = None
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    test_cases: Optional[list] = None
    tags: Optional[list] = None
    company_tags: Optional[list] = None
    frequency: int = 0
    is_hot: bool = False
    created_at: datetime


class QuestionListResponse(BaseModel):
    """题目列表响应"""
    total: int
    page: int
    page_size: int
    items: List[QuestionListItem]


# ==================== 作答相关 ====================

class AnswerSubmitRequest(BaseModel):
    """提交答案请求"""
    answer: str = Field(..., description="用户答案")
    time_spent: Optional[int] = Field(None, ge=0, description="用时（秒）")


class AnswerSubmitResponse(BaseModel):
    """提交答案响应"""
    is_correct: bool = Field(..., description="是否正确")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    explanation: Optional[str] = Field(None, description="答案解析")


# ==================== 个人统计 ====================

class PracticeStats(BaseModel):
    """刷题统计"""
    total_practiced: int = Field(0, description="总刷题数")
    correct_count: int = Field(0, description="正确数量")
    wrong_count: int = Field(0, description="错误数量")
    accuracy_rate: float = Field(0.0, description="正确率（百分比）")


# ==================== 错题本 ====================

class WrongQuestionItem(BaseModel):
    """错题项"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question_id: int
    question_title: str
    difficulty: Optional[str] = None
    wrong_count: int = 1
    last_wrong_at: datetime
    is_mastered: bool = False
    notes: Optional[str] = None


class WrongQuestionListResponse(BaseModel):
    """错题列表响应"""
    total: int
    items: List[WrongQuestionItem]


# ==================== 收藏相关 ====================

class FavoriteQuestionItem(BaseModel):
    """收藏题目项"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question_id: int
    question_title: str
    difficulty: Optional[str] = None
    type: str
    practiced_at: Optional[datetime] = None


class FavoriteQuestionListResponse(BaseModel):
    """收藏列表响应"""
    total: int
    items: List[FavoriteQuestionItem]
