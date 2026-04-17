# app/models/interview.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, BigInteger, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Interview(Base):
    """面试记录表"""
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("applications.id"), nullable=False, comment="关联投递记录")
    
    round: Mapped[int] = mapped_column(Integer, default=1, comment="第几轮面试")
    interview_type: Mapped[Optional[str]] = mapped_column(
        Enum('phone', 'video', 'onsite', 'ai_mock'),
        nullable=True,
        comment="面试类型"
    )
    
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="面试时间")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, comment="预计时长（分钟）")
    
    status: Mapped[str] = mapped_column(
        Enum('scheduled', 'completed', 'cancelled', 'no_show'),
        default='scheduled',
        comment="状态"
    )
    
    interviewer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="面试官")
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="面试地点/链接")
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="面试反馈")
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="自我评分1-10")
    questions_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="面试问题记录")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    application: Mapped["Application"] = relationship("Application", back_populates="interviews")
    
    def __repr__(self) -> str:
        return f"<Interview Round {self.round}>"


class AIInterview(Base):
    """AI面试会话"""
    __tablename__ = "ai_interviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    application_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("applications.id"), nullable=True, comment="关联投递记录")
    
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="目标岗位名称")
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="目标岗位JD")
    
    interview_type: Mapped[str] = mapped_column(
        Enum('technical', 'behavioral', 'comprehensive'),
        default='comprehensive',
        comment="面试类型"
    )
    
    status: Mapped[str] = mapped_column(
        Enum('ongoing', 'completed', 'aborted'),
        default='ongoing'
    )
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    total_questions: Mapped[int] = mapped_column(Integer, default=0, comment="总问题数")
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="综合评分0-100")
    
    strength_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="优势分析")
    weakness_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="待改进点")
    improvement_suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="改进建议")
    
    transcript: Mapped[Optional[list]] = mapped_column(String(500), nullable=True, comment="完整对话记录JSON")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="ai_interviews")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="ai_interviews")
    qa_records: Mapped[List["AIInterviewQA"]] = relationship("AIInterviewQA", back_populates="interview")
    
    def __repr__(self) -> str:
        return f"<AIInterview {self.job_title}>"


class AIInterviewQA(Base):
    """AI面试问答详情"""
    __tablename__ = "ai_interview_qa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    interview_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ai_interviews.id"), nullable=False)
    
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, comment="问题序号")
    question: Mapped[str] = mapped_column(Text, nullable=False, comment="AI问题")
    
    question_type: Mapped[Optional[str]] = mapped_column(
        Enum('intro', 'tech', 'behavior', 'project', 'salary', 'end'),
        nullable=True,
        comment="问题类型"
    )
    
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户回答")
    answer_audio_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="回答音频URL")
    
    evaluation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="该题评分")
    evaluation_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="评价详情")
    suggested_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="参考答案")
    
    response_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="回答用时")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    interview: Mapped["AIInterview"] = relationship("AIInterview", back_populates="qa_records")
    
    def __repr__(self) -> str:
        return f"<AIInterviewQA Q{self.sequence}>"
