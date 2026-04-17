# app/schemas/dashboard.py
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class QuickAction(BaseModel):
    """快速操作按钮"""
    name: str = Field(..., description="操作名称")
    path: str = Field(..., description="跳转路径")
    icon: str = Field(..., description="图标名称")
    description: Optional[str] = Field(None, description="描述")


class StatisticsSummary(BaseModel):
    """统计数据摘要"""
    total_applications: int = Field(0, description="总投递数")
    total_ai_interviews: int = Field(0, description="AI面试总数")
    total_practices: int = Field(0, description="刷题总数")
    favorite_jobs: int = Field(0, description="收藏岗位数")
    accuracy_rate: float = Field(0.0, description="正确率百分比")
    completed_interviews: int = Field(0, description="完成面试数")


class DashboardOverviewResponse(BaseModel):
    """首页概览响应"""
    quick_actions: List[QuickAction] = Field([], description="快速操作列表")
    statistics: StatisticsSummary = Field(..., description="统计数据")


class GrowthCurveDataPoint(BaseModel):
    """成长曲线数据点"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    applications: int = Field(0, description="投递数")
    ai_interviews: int = Field(0, description="AI面试数")
    practices: int = Field(0, description="刷题数")
    accuracy: Optional[float] = Field(None, description="正确率")


class GrowthCurveResponse(BaseModel):
    """成长曲线响应"""
    dates: List[str] = Field([], description="日期列表")
    metrics: Dict[str, List] = Field({}, description="指标数据")
    summary: Dict[str, float] = Field({}, description="汇总统计")


class ActivityRecord(BaseModel):
    """活动记录"""
    id: int = Field(..., description="活动ID")
    type: str = Field(..., description="活动类型")
    title: str = Field(..., description="活动标题")
    description: str = Field(..., description="活动描述")
    icon: str = Field(..., description="图标")
    color: str = Field("blue", description="颜色主题")
    created_at: datetime = Field(..., description="创建时间")


class ActivitiesResponse(BaseModel):
    """活动列表响应"""
    activities: List[ActivityRecord] = Field([], description="活动列表")
    total: int = Field(0, description="总数")
