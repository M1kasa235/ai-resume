# app/services/job_service.py
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, text
from fastapi import HTTPException, status

from app.models.job import Job, JobCategory, UserFavoriteJob
from app.schemas.job import (
    JobCreate, JobUpdate, JobSearchParams, JobCategoryCreate, JobCategoryUpdate
)

class JobService:
    """岗位服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: int) -> Optional[Job]:
        """通过ID获取岗位"""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_detail(self, job_id: int, user_id: Optional[int] = None) -> Optional[Job]:
        """获取岗位详情（包含收藏状态）"""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job and user_id:
            fav_result = await self.db.execute(
                select(UserFavoriteJob).where(
                    and_(UserFavoriteJob.user_id == user_id, UserFavoriteJob.job_id == job_id)
                )
            )
            job.is_favorited = fav_result.scalar_one_or_none() is not None

        return job

    async def create(self, job_data: JobCreate, publisher_id: Optional[int] = None) -> Job:
        """创建岗位"""
        db_job = Job(
            **job_data.model_dump(exclude_unset=True),
            publisher_id=publisher_id,
            published_at=datetime.utcnow()
        )
        self.db.add(db_job)
        await self.db.commit()
        await self.db.refresh(db_job)
        return db_job

    async def update(self, job: Job, update_data: JobUpdate) -> Job:
        """更新岗位"""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(job, field, value)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete(self, job: Job) -> None:
        """删除岗位（软删除）"""
        job.is_active = False
        await self.db.commit()

    async def hard_delete(self, job: Job) -> None:
        """硬删除岗位"""
        await self.db.delete(job)
        await self.db.commit()

    async def increment_view_count(self, job_id: int) -> None:
        """增加浏览量"""
        await self.db.execute(
            text("UPDATE jobs SET view_count = view_count + 1 WHERE id = :job_id"),
            {"job_id": job_id}
        )
        await self.db.commit()

    async def search(self, params: JobSearchParams, user_id: Optional[int] = None) -> Tuple[int, List[Job]]:
        """搜索岗位"""
        from sqlalchemy.orm import selectinload
        
        # 使用 selectinload 预加载 category 关系，避免懒加载导致的异步问题
        query = select(Job).options(selectinload(Job.category)).where(Job.is_active == True)
        count_query = select(func.count(Job.id)).where(Job.is_active == True)

        # 关键词搜索
        if params.keyword:
            keyword_filter = or_(
                Job.title.contains(params.keyword),
                Job.company_name.contains(params.keyword),
                Job.description.contains(params.keyword),
                Job.requirements.contains(params.keyword)
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        # 城市筛选
        if params.city:
            query = query.where(Job.city == params.city)
            count_query = count_query.where(Job.city == params.city)

        # 分类筛选
        if params.category_id:
            query = query.where(Job.category_id == params.category_id)
            count_query = count_query.where(Job.category_id == params.category_id)

        # 薪资范围
        if params.salary_min is not None:
            query = query.where(Job.salary_max >= params.salary_min)
            count_query = count_query.where(Job.salary_max >= params.salary_min)
        if params.salary_max is not None:
            query = query.where(Job.salary_min <= params.salary_max)
            count_query = count_query.where(Job.salary_min <= params.salary_max)

        # 经验范围
        if params.experience_min is not None:
            exp_filter = or_(Job.experience_max >= params.experience_min, Job.experience_max.is_(None))
            query = query.where(exp_filter)
            count_query = count_query.where(exp_filter)
        if params.experience_max is not None:
            exp_filter = or_(Job.experience_min <= params.experience_max, Job.experience_min.is_(None))
            query = query.where(exp_filter)
            count_query = count_query.where(exp_filter)

        # 学历
        if params.education:
            edu_filter = or_(Job.education_requirement == params.education, Job.education_requirement == "unlimited")
            query = query.where(edu_filter)
            count_query = count_query.where(edu_filter)

        # 公司阶段
        if params.company_stage:
            query = query.where(Job.company_stage == params.company_stage)
            count_query = count_query.where(Job.company_stage == params.company_stage)

        # 技能标签
        if params.skills:
            for skill in params.skills:
                skill_filter = Job.skills_required.contains(skill)
                query = query.where(skill_filter)
                count_query = count_query.where(skill_filter)

        # 只看急聘
        if params.only_urgent:
            query = query.where(Job.is_urgent == True)
            count_query = count_query.where(Job.is_urgent == True)

        # 排序（使用白名单防止无效字段）
        allowed_sort_fields = {
            "published_at": Job.published_at,
            "salary_min": Job.salary_min,
            "salary_max": Job.salary_max,
            "view_count": Job.view_count,
            "apply_count": Job.apply_count,
            "created_at": Job.created_at,
        }
        sort_field = allowed_sort_fields.get(params.sort_by, Job.published_at)
        
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        # 分页
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        # 关键修复：在会话关闭前访问所有属性，确保数据已加载
        for job in jobs:
            # 触发所有字段的加载
            _ = job.id
            _ = job.title
            _ = job.company_name
            _ = job.city
            _ = job.salary_min
            _ = job.salary_max
            _ = job.salary_months
            _ = job.published_at
            _ = job.created_at
            _ = job.updated_at
            _ = job.is_active
            _ = job.view_count
            _ = job.apply_count
            _ = job.salary_display  # 触发 @property
            _ = job.experience_display  # 触发 @property

        # 检查收藏状态（动态添加属性）
        if user_id and jobs:
            job_ids = [j.id for j in jobs]
            fav_result = await self.db.execute(
                select(UserFavoriteJob.job_id).where(
                    and_(UserFavoriteJob.user_id == user_id, UserFavoriteJob.job_id.in_(job_ids))
                )
            )
            favorited_ids = {row[0] for row in fav_result.all()}
            for job in jobs:
                # 使用 __dict__ 直接设置属性，避免 SQLAlchemy 警告
                job.__dict__['is_favorited'] = job.id in favorited_ids

        return total, list(jobs)

    async def get_hot_jobs(self, limit: int = 10) -> List[Job]:
        """获取热门岗位"""
        result = await self.db.execute(
            select(Job).where(Job.is_active == True)
            .order_by(desc(Job.view_count + Job.apply_count * 10))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_jobs(self, limit: int = 10) -> List[Job]:
        """获取最新岗位"""
        result = await self.db.execute(
            select(Job).where(Job.is_active == True)
            .order_by(desc(Job.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_statistics(self) -> dict:
        """获取岗位统计数据"""
        total_result = await self.db.execute(select(func.count(Job.id)).where(Job.is_active == True))
        total = total_result.scalar()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.db.execute(select(func.count(Job.id)).where(Job.created_at >= today))
        today_count = today_result.scalar()

        city_result = await self.db.execute(
            select(Job.city, func.count(Job.id)).where(Job.is_active == True)
            .group_by(Job.city).order_by(desc(func.count(Job.id))).limit(10)
        )
        city_stats = [{"city": row[0], "count": row[1]} for row in city_result.all()]

        return {"total": total, "today_new": today_count, "top_cities": city_stats}


class JobCategoryService:
    """岗位分类服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Optional[JobCategory]:
        """通过ID获取分类"""
        result = await self.db.execute(select(JobCategory).where(JobCategory.id == category_id))
        return result.scalar_one_or_none()

    async def get_all(self, only_active: bool = True) -> List[JobCategory]:
        """获取所有分类"""
        query = select(JobCategory)
        if only_active:
            query = query.where(JobCategory.is_active == True)
        query = query.order_by(JobCategory.sort_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tree(self) -> List[JobCategory]:
        """获取分类树（只返回顶级分类，包含子分类）"""
        result = await self.db.execute(
            select(JobCategory).where(and_(JobCategory.parent_id.is_(None), JobCategory.is_active == True))
            .order_by(JobCategory.sort_order)
        )
        return list(result.scalars().all())

    async def create(self, category_data: JobCategoryCreate) -> JobCategory:
        """创建分类"""
        db_category = JobCategory(**category_data.model_dump())
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category

    async def update(self, category: JobCategory, update_data: JobCategoryUpdate) -> JobCategory:
        """更新分类"""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: JobCategory) -> None:
        """删除分类（软删除）"""
        category.is_active = False
        await self.db.commit()


class UserFavoriteJobService:
    """用户收藏服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_favorite(self, user_id: int, job_id: int) -> UserFavoriteJob:
        """添加收藏"""
        result = await self.db.execute(
            select(UserFavoriteJob).where(
                and_(UserFavoriteJob.user_id == user_id, UserFavoriteJob.job_id == job_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="已经收藏过该岗位")

        job_result = await self.db.execute(select(Job).where(Job.id == job_id))
        if not job_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="岗位不存在")

        favorite = UserFavoriteJob(user_id=user_id, job_id=job_id)
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def remove_favorite(self, user_id: int, job_id: int) -> None:
        """取消收藏"""
        result = await self.db.execute(
            select(UserFavoriteJob).where(
                and_(UserFavoriteJob.user_id == user_id, UserFavoriteJob.job_id == job_id)
            )
        )
        favorite = result.scalar_one_or_none()
        if favorite:
            await self.db.delete(favorite)
            await self.db.commit()

    async def get_user_favorites(self, user_id: int, page: int = 1, page_size: int = 20) -> Tuple[int, List[UserFavoriteJob]]:
        """获取用户收藏列表"""
        from sqlalchemy.orm import selectinload
        
        count_result = await self.db.execute(
            select(func.count(UserFavoriteJob.id)).where(UserFavoriteJob.user_id == user_id)
        )
        total = count_result.scalar()

        result = await self.db.execute(
            select(UserFavoriteJob)
            .options(selectinload(UserFavoriteJob.job))
            .where(UserFavoriteJob.user_id == user_id)
            .order_by(desc(UserFavoriteJob.created_at))
            .offset((page - 1) * page_size).limit(page_size)
        )
        return total, list(result.scalars().all())

    async def is_favorited(self, user_id: int, job_id: int) -> bool:
        """检查是否已收藏"""
        result = await self.db.execute(
            select(UserFavoriteJob).where(
                and_(UserFavoriteJob.user_id == user_id, UserFavoriteJob.job_id == job_id)
            )
        )
        return result.scalar_one_or_none() is not None