# app/models/job.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, DateTime, Enum, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class JobCategory(Base):
    """岗位分类"""
    __tablename__ = "job_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="分类编码")
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_categories.id"), nullable=True, comment="父分类ID")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 自关联关系
    children: Mapped[List["JobCategory"]] = relationship("JobCategory", back_populates="parent", remote_side=[id])
    parent: Mapped[Optional["JobCategory"]] = relationship("JobCategory", back_populates="children", remote_side=[parent_id])
    
    # 与岗位的关系
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="category")

    def __repr__(self) -> str:
        return f"<JobCategory {self.name}>"


class Job(Base):
    """岗位表"""
    __tablename__ = "jobs"

    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 基础信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="职位标题", index=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_categories.id"), nullable=True, comment="分类ID")

    # 公司信息
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="公司名称", index=True)
    company_logo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="公司Logo")
    company_stage: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="公司阶段")
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="公司规模")

    # 职位描述
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="职位描述")
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="岗位要求")

    # 薪资信息
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="最低薪资")
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="最高薪资")
    salary_months: Mapped[int] = mapped_column(Integer, default=12, comment="薪几个月")

    # 地点信息
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="工作城市", index=True)
    district: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="区县")
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="详细地址")

    # 经验学历要求
    experience_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="最低经验要求（年）")
    experience_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="最高经验要求（年）")
    education_requirement: Mapped[str] = mapped_column(String(20), default="unlimited", comment="学历要求")

    # 技能标签
    skills_required: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="所需技能")
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="标签（双休、远程等）")

    # 来源信息
    source: Mapped[str] = mapped_column(String(20), default="internal", comment="来源")
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="原始链接")
    publisher_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True, comment="发布者ID")

    # 统计数据
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览量")
    apply_count: Mapped[int] = mapped_column(Integer, default=0, comment="申请次数")

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效", index=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否急聘")

    # 时间
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="发布时间", index=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    category: Mapped[Optional["JobCategory"]] = relationship("JobCategory", back_populates="jobs")
    publisher: Mapped[Optional["User"]] = relationship("User", back_populates="published_jobs")
    favorited_by: Mapped[List["UserFavoriteJob"]] = relationship("UserFavoriteJob", back_populates="job")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job")

    def __repr__(self) -> str:
        return f"<Job {self.title}@{self.company_name}>"

    @property
    def salary_display(self) -> str:
        """薪资显示文本"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min}k-{self.salary_max}k·{self.salary_months}薪"
        elif self.salary_min:
            return f"{self.salary_min}k以上·{self.salary_months}薪"
        elif self.salary_max:
            return f"{self.salary_max}k以下·{self.salary_months}薪"
        return "薪资面议"

    @property
    def experience_display(self) -> str:
        """经验显示文本"""
        if self.experience_min is not None and self.experience_max is not None:
            if self.experience_min == self.experience_max:
                return f"{self.experience_min}年"
            return f"{self.experience_min}-{self.experience_max}年"
        elif self.experience_min is not None:
            return f"{self.experience_min}年以上"
        elif self.experience_max is not None:
            return f"{self.experience_max}年以下"
        return "经验不限"


class UserFavoriteJob(Base):
    """用户收藏岗位"""
    __tablename__ = "user_favorite_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("jobs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="favorite_jobs")
    job: Mapped["Job"] = relationship("Job", back_populates="favorited_by")

    __table_args__ = (
        Index("uk_user_job", "user_id", "job_id", unique=True),
    )