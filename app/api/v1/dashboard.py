# app/api/v1/dashboard.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    GrowthCurveResponse,
    ActivitiesResponse
)

router = APIRouter(prefix="/dashboard", tags=["首页"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页概览数据
    
    返回快速操作按钮和用户统计数据
    """
    service = DashboardService(db)
    data = await service.get_overview(current_user.id)
    return data


@router.get("/growth-curve", response_model=GrowthCurveResponse)
async def get_growth_curve(
    days: int = Query(default=30, ge=7, le=90, description="查询天数，范围7-90天"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取个人成长曲线数据
    
    - **days**: 查询天数（默认30天，范围7-90天）
    
    返回指定天数内的投递、AI面试、刷题等指标的趋势数据
    """
    service = DashboardService(db)
    data = await service.get_growth_curve(current_user.id, days)
    return data


@router.get("/activities", response_model=ActivitiesResponse)
async def get_recent_activities(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取个人最新动态
    
    - **limit**: 返回数量限制（默认10条，范围1-50）
    
    聚合显示最近的投递、AI面试、刷题、收藏等活动记录
    """
    service = DashboardService(db)
    activities = await service.get_activities(current_user.id, limit)
    
    return {
        "activities": activities,
        "total": len(activities)
    }
