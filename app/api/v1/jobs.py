# app/api/v1/job.py
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_active_user
from app.schemas.job import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobSearchParams, JobCategoryCreate, JobCategoryUpdate, JobCategoryResponse,
    JobCategoryTree
)
from app.schemas.common import PageResponse
from app.services.job_service import JobService, JobCategoryService, UserFavoriteJobService
from app.models.user import User

router = APIRouter(prefix="/jobs", tags=["岗位管理"])

# ==================== 岗位CRUD接口 ====================

@router.get("/list", response_model=PageResponse[JobResponse])
async def list_jobs(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    city: Optional[str] = Query(None, description="城市"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    salary_min: Optional[int] = Query(None, ge=0, description="最低薪资"),
    salary_max: Optional[int] = Query(None, ge=0, description="最高薪资"),
    experience_min: Optional[int] = Query(None, ge=0, le=50, description="最低经验"),
    experience_max: Optional[int] = Query(None, ge=0, le=50, description="最高经验"),
    education: Optional[str] = Query(None, description="学历要求"),
    company_stage: Optional[str] = Query(None, description="公司阶段"),
    skills: Optional[List[str]] = Query(None, description="技能标签"),
    sort_by: str = Query("published_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    only_urgent: bool = Query(False, description="只看急聘"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取岗位列表（支持多维度筛选）"""
    service = JobService(db)
    search_params = JobSearchParams(
        keyword=keyword, city=city, category_id=category_id,
        salary_min=salary_min, salary_max=salary_max,
        experience_min=experience_min, experience_max=experience_max,
        education=education, company_stage=company_stage, skills=skills,
        sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size, only_urgent=only_urgent
    )
    user_id = current_user.id if current_user else None
    total, jobs = await service.search(search_params, user_id=user_id)
    
    # 关键修复：在会话关闭前手动转换为 Pydantic 模型
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    return PageResponse(total=total, items=job_responses, page=page, page_size=page_size)

@router.get("/hot")
async def get_hot_jobs(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    """获取热门岗位"""
    service = JobService(db)
    return await service.get_hot_jobs(limit=limit)

@router.get("/latest")
async def get_latest_jobs(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    """获取最新岗位"""
    service = JobService(db)
    return await service.get_latest_jobs(limit=limit)

@router.get("/statistics")
async def get_job_statistics(db: AsyncSession = Depends(get_db)):
    """获取岗位统计数据"""
    service = JobService(db)
    return await service.get_statistics()

@router.get("/{job_id}")
async def get_job_detail(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取岗位详情"""
    service = JobService(db)
    await service.increment_view_count(job_id)
    user_id = current_user.id if current_user else None
    job = await service.get_detail(job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建岗位"""
    service = JobService(db)
    return await service.create(job_data, publisher_id=current_user.id)

@router.put("/{job_id}")
async def update_job(
    job_id: int,
    update_data: JobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新岗位"""
    service = JobService(db)
    job = await service.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publisher_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此岗位")
    return await service.update(job, update_data)

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除岗位（软删除）"""
    service = JobService(db)
    job = await service.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.publisher_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此岗位")
    await service.delete(job)
    return {"message": "岗位已删除"}

# ==================== 岗位分类接口 ====================

@router.get("/categories/tree")
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    """获取岗位分类树"""
    service = JobCategoryService(db)
    return await service.get_tree()

@router.get("/categories/list")
async def get_category_list(db: AsyncSession = Depends(get_db)):
    """获取所有分类列表"""
    service = JobCategoryService(db)
    return await service.get_all()

@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: JobCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建分类（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    service = JobCategoryService(db)
    return await service.create(category_data)

@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    update_data: JobCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新分类（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = JobCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    updated = await service.update(category, update_data)
    return updated

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除分类（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = JobCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    await service.delete(category)
    return {"message": "分类已删除"}

# ==================== 收藏相关接口 ====================

@router.post("/{job_id}/favorite")
async def add_favorite(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """收藏岗位"""
    service = UserFavoriteJobService(db)
    await service.add_favorite(current_user.id, job_id)
    return {"message": "收藏成功"}

@router.delete("/{job_id}/favorite")
async def remove_favorite(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """取消收藏"""
    service = UserFavoriteJobService(db)
    await service.remove_favorite(current_user.id, job_id)
    return {"message": "已取消收藏"}

@router.get("/user/favorites", response_model=PageResponse[JobResponse])
async def get_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的收藏列表"""
    service = UserFavoriteJobService(db)
    total, favorites = await service.get_user_favorites(current_user.id, page=page, page_size=page_size)
    # 提取 job 对象
    jobs = [fav.job for fav in favorites]
    return PageResponse(total=total, items=jobs, page=page, page_size=page_size)

@router.get("/{job_id}/favorite/status")
async def check_favorite_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """检查是否已收藏"""
    service = UserFavoriteJobService(db)
    is_fav = await service.is_favorited(current_user.id, job_id)
    return {"is_favorited": is_fav}
