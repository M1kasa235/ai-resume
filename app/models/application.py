# app/models/application.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, BigInteger, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Application(Base):
    """投递记录表"""
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    job_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("jobs.id"), nullable=True, comment="关联系统岗位ID")
    
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="公司名称")
    job_title: Mapped[str] = mapped_column(String(100), nullable=False, comment="职位名称")
    jd_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="职位描述文本")
    jd_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="职位链接")
    salary_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="薪资范围")
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="城市")
    
    contact_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="联系人")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="联系人电话")
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="联系人邮箱")
    
    status: Mapped[str] = mapped_column(
        Enum('interested', 'applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn'),
        default='interested',
        comment="状态"
    )
    priority: Mapped[str] = mapped_column(
        Enum('low', 'normal', 'high', 'urgent'),
        default='normal',
        comment="优先级"
    )
    
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="投递时间")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="applications")
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="application")
    ai_interviews: Mapped[list["AIInterview"]] = relationship("AIInterview", back_populates="application")
    
    def __repr__(self) -> str:
        return f"<Application {self.job_title}@{self.company_name}>"
