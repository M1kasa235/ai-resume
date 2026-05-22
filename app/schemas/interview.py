"""AI 面试相关 Schema"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ── 请求 ──

class AIInterviewStartRequest(BaseModel):
    job_title: Optional[str] = Field(None, description="目标岗位名称")
    company_name: Optional[str] = Field(None, description="目标公司名称")
    interview_type: Optional[str] = Field("comprehensive", description="面试类型: technical / hr / comprehensive")
    job_description: Optional[str] = Field(None, description="岗位 JD 描述，用于精准出题")


class AIInterviewReplyRequest(BaseModel):
    session_id: str = Field(..., description="面试会话 ID")
    message: str = Field(..., description="用户回答内容")


# ── 消息/会话 ──

class AIInterviewReplyResponse(BaseModel):
    session_id: str = Field(..., description="面试会话 ID")
    reply: str = Field(..., description="AI 面试官回复")


class AIInterviewMessageSchema(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIInterviewSessionResponse(BaseModel):
    session_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    interview_type: Optional[str] = None
    messages: List[AIInterviewMessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ── 评估报告 ──

class QAEvaluation(BaseModel):
    sequence: int
    question: str
    answer: Optional[str] = None
    score: Optional[int] = Field(None, description="该题评分 1-10")
    comment: Optional[str] = Field(None, description="点评")
    suggested_answer: Optional[str] = Field(None, description="参考回答")


class AIInterviewEndResponse(BaseModel):
    session_id: str
    status: str
    total_questions: int = 0
    overall_score: Optional[int] = None
    strength_analysis: Optional[str] = None
    weakness_analysis: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    report_markdown: Optional[str] = Field(None, description="完整 Markdown 报告")
    evaluations: List[QAEvaluation] = Field(default_factory=list, description="逐题评估")


class AIInterviewReportResponse(BaseModel):
    session_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    interview_type: Optional[str] = None
    status: str
    total_questions: int = 0
    overall_score: Optional[int] = None
    strength_analysis: Optional[str] = None
    weakness_analysis: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    report_markdown: Optional[str] = None
    evaluations: List[QAEvaluation] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIInterviewReportListItem(BaseModel):
    session_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    interview_type: Optional[str] = None
    status: str
    total_questions: int = 0
    overall_score: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIInterviewReportListResponse(BaseModel):
    total: int
    items: List[AIInterviewReportListItem]
