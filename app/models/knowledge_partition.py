"""知识库分区模型 — 用户可自定义知识库类别"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class KnowledgePartition(Base):
    """知识库分区定义

    当前默认分区：job / resume_guide / interview
    doc_key 对应 Chroma metadata 中的 doc_type 字段
    """

    __tablename__ = "knowledge_partitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="分区唯一键，对应 Chroma doc_type"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="分区显示名称"
    )
    description: Mapped[str] = mapped_column(
        Text, default="", comment="分区描述"
    )
    created_by: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="创建人用户 ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )