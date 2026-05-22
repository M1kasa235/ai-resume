# app/models/resume_version.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ResumeVersion(Base):
    """简历版本管理表"""
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户ID")
    version: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号（按用户自增）")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="版本内容（完整简历文本）")
    source: Mapped[str] = mapped_column(String(20), default="manual", comment="来源: upload/optimize/polish/manual")
    source_file: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="源文件路径")
    job_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="关联岗位ID")
    summary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="版本说明")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
