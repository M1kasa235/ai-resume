# app/models/user.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # 登录凭证
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="用户名")
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, comment="手机号")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="密码哈希")

    # 基础信息
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="头像URL")
    real_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="真实姓名")
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="性别")

    # 求职相关信息（预留字段，后续完善）
    current_city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="当前城市")
    target_city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="目标城市")
    work_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="工作年限")
    education: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="学历")

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否管理员")

    # 时间戳
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后登录时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关系
    favorite_jobs: Mapped[List["UserFavoriteJob"]] = relationship("UserFavoriteJob", back_populates="user")
    published_jobs: Mapped[List["Job"]] = relationship("Job", back_populates="publisher")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="user")
    ai_interviews: Mapped[List["AIInterview"]] = relationship("AIInterview", back_populates="user")
    practices: Mapped[List["UserPractice"]] = relationship("UserPractice", back_populates="user")
    wrong_questions: Mapped[List["UserWrongQuestion"]] = relationship("UserWrongQuestion", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.username}>"