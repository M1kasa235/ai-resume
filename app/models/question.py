# app/models/question.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, BigInteger, Enum, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class QuestionCategory(Base):
    """题目分类"""
    __tablename__ = "question_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    type: Mapped[str] = mapped_column(
        Enum('tech', 'algorithm', 'behavior', 'hr'),
        nullable=False,
        comment="题目类型"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("question_categories.id"), nullable=True, comment="父分类ID")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 自关联关系
    children: Mapped[List["QuestionCategory"]] = relationship("QuestionCategory", back_populates="parent", remote_side=[id])
    parent: Mapped[Optional["QuestionCategory"]] = relationship("QuestionCategory", back_populates="children", remote_side=[parent_id])
    
    # 与题目的关系
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="category")

    def __repr__(self) -> str:
        return f"<QuestionCategory {self.name}>"


class Question(Base):
    """题目表"""
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("question_categories.id"), nullable=False)
    
    type: Mapped[str] = mapped_column(
        Enum('single_choice', 'multiple_choice', 'essay', 'coding', 'open'),
        nullable=False,
        comment="题型"
    )
    difficulty: Mapped[str] = mapped_column(
        Enum('easy', 'medium', 'hard'),
        default='medium',
        nullable=True,
        comment="难度"
    )
    
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="题目标题")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="题目内容")
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="选项（选择题）")
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="正确答案")
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="答案解析")
    
    code_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="代码题模板")
    test_cases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="测试用例（代码题）")
    
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="标签")
    company_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="考察该公司")
    
    frequency: Mapped[int] = mapped_column(Integer, default=0, comment="出现频率")
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否高频题")
    
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="题目来源")
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True, comment="创建者")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    category: Mapped["QuestionCategory"] = relationship("QuestionCategory", back_populates="questions")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    practices: Mapped[List["UserPractice"]] = relationship("UserPractice", back_populates="question")
    wrong_records: Mapped[List["UserWrongQuestion"]] = relationship("UserWrongQuestion", back_populates="question")

    def __repr__(self) -> str:
        return f"<Question {self.title}>"


class UserPractice(Base):
    """用户刷题记录"""
    __tablename__ = "user_practices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    
    status: Mapped[str] = mapped_column(
        Enum('correct', 'wrong', 'skipped', 'unanswered'),
        default='unanswered',
        nullable=True
    )
    
    user_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户答案")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否收藏")
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="用时（秒）")
    
    practiced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    review_count: Mapped[int] = mapped_column(Integer, default=0, comment="复习次数")
    next_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="下次复习时间")
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="practices")
    question: Mapped["Question"] = relationship("Question", back_populates="practices")

    def __repr__(self) -> str:
        return f"<UserPractice user={self.user_id} question={self.question_id}>"


class UserWrongQuestion(Base):
    """用户错题本"""
    __tablename__ = "user_wrong_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    
    wrong_count: Mapped[int] = mapped_column(Integer, default=1, comment="错误次数")
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已掌握")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错题笔记")
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="wrong_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="wrong_records")

    def __repr__(self) -> str:
        return f"<UserWrongQuestion user={self.user_id} question={self.question_id}>"
