# app/services/dashboard_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from sqlalchemy import func, select, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.job import Job


class DashboardService:
    """首页业务逻辑服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: int) -> Dict:
        """
        获取首页概览数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            包含快速操作和统计数据的字典
        """
        # 获取统计数据
        statistics = await self._get_statistics(user_id)
        
        # 定义快速操作
        quick_actions = [
            {
                "name": "岗位浏览",
                "path": "/jobs",
                "icon": "briefcase",
                "description": "浏览最新岗位"
            },
            {
                "name": "工作台",
                "path": "/workbench",
                "icon": "work",
                "description": "查看我的简历"
            },
            {
                "name": "AI面试",
                "path": "/ai-interviews",
                "icon": "robot",
                "description": "开始AI模拟面试"
            },
            {
                "name": "刷题练习",
                "path": "/practice",
                "icon": "book",
                "description": "练习面试题目"
            },

        ]
        
        return {
            "quick_actions": quick_actions,
            "statistics": statistics
        }

    async def _get_statistics(self, user_id: int) -> Dict:
        """获取用户统计数据"""
        from app.models.job import UserFavoriteJob
        
        # 由于 Application 模型可能还未定义，使用原始SQL方式
        # 这里先返回默认值，后续需要根据实际模型调整
        total_applications = await self._count_applications(user_id)
        total_ai_interviews = await self._count_ai_interviews(user_id)
        total_practices = await self._count_practices(user_id)
        favorite_jobs = await self._count_favorite_jobs(user_id)
        accuracy_rate = await self._calculate_accuracy(user_id)
        completed_interviews = await self._count_completed_interviews(user_id)
        
        return {
            "total_applications": total_applications,
            "total_ai_interviews": total_ai_interviews,
            "total_practices": total_practices,
            "favorite_jobs": favorite_jobs,
            "accuracy_rate": round(accuracy_rate, 2),
            "completed_interviews": completed_interviews
        }

    async def _count_applications(self, user_id: int) -> int:
        """统计投递数量"""
        try:
            from app.models import Application
            stmt = select(func.count()).select_from(Application).where(
                Application.user_id == user_id
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except (ImportError, AttributeError):
            return 0

    async def _count_ai_interviews(self, user_id: int) -> int:
        """统计AI面试数量"""
        try:
            from app.models import AIInterview
            stmt = select(func.count()).select_from(AIInterview).where(
                AIInterview.user_id == user_id
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except (ImportError, AttributeError):
            return 0

    async def _count_practices(self, user_id: int) -> int:
        """统计刷题数量"""
        try:
            from app.models import UserPractice
            stmt = select(func.count()).select_from(UserPractice).where(
                UserPractice.user_id == user_id
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except (ImportError, AttributeError):
            return 0

    async def _count_favorite_jobs(self, user_id: int) -> int:
        """统计收藏岗位数量"""
        from app.models.job import UserFavoriteJob
        stmt = select(func.count()).select_from(UserFavoriteJob).where(
            UserFavoriteJob.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _calculate_accuracy(self, user_id: int) -> float:
        """计算正确率"""
        try:
            from app.models import UserPractice
            stmt = select(
                func.count(case((UserPractice.status == 'correct', 1))),
                func.count()
            ).where(UserPractice.user_id == user_id)
            
            result = await self.db.execute(stmt)
            correct, total = result.one()
            
            if total == 0:
                return 0.0
            return (correct / total) * 100
        except (ImportError, AttributeError):
            return 0.0

    async def _count_completed_interviews(self, user_id: int) -> int:
        """统计完成的AI面试数量"""
        try:
            from app.models import AIInterview
            stmt = select(func.count()).select_from(AIInterview).where(
                AIInterview.user_id == user_id,
                AIInterview.status == 'completed'
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        except (ImportError, AttributeError):
            return 0

    async def get_growth_curve(self, user_id: int, days: int = 30) -> Dict:
        """
        获取成长曲线数据
        
        Args:
            user_id: 用户ID
            days: 天数，默认30天
            
        Returns:
            包含日期序列和各指标数据的字典
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 生成日期列表
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        # 获取各指标数据
        applications_data = await self._get_daily_applications(user_id, start_date, end_date)
        ai_interviews_data = await self._get_daily_ai_interviews(user_id, start_date, end_date)
        practices_data = await self._get_daily_practices(user_id, start_date, end_date)
        accuracy_data = await self._get_daily_accuracy(user_id, start_date, end_date)
        
        # 填充数据到日期列表
        applications_list = [applications_data.get(date, 0) for date in dates]
        ai_interviews_list = [ai_interviews_data.get(date, 0) for date in dates]
        practices_list = [practices_data.get(date, 0) for date in dates]
        accuracy_list = [accuracy_data.get(date, None) for date in dates]
        
        # 计算汇总统计
        valid_accuracies = [a for a in accuracy_list if a is not None]
        summary = {
            "avg_applications": sum(applications_list) / len(applications_list) if applications_list else 0,
            "avg_practices": sum(practices_list) / len(practices_list) if practices_list else 0,
            "total_applications": sum(applications_list),
            "total_practices": sum(practices_list),
            "avg_accuracy": sum(valid_accuracies) / len(valid_accuracies) if valid_accuracies else 0
        }
        
        return {
            "dates": dates,
            "metrics": {
                "applications": applications_list,
                "ai_interviews": ai_interviews_list,
                "practices": practices_list,
                "accuracy": accuracy_list
            },
            "summary": summary
        }

    async def _get_daily_applications(self, user_id: int, start_date: datetime, end_date: datetime) -> dict[Any,
    Callable[..., int]] | dict[Any, Any]:
        """获取每日投递数"""
        try:
            from app.models import Application
            stmt = select(
                func.date(Application.applied_at).label('date'),
                func.count().label('count')
            ).where(
                Application.user_id == user_id,
                Application.applied_at >= start_date,
                Application.applied_at <= end_date
            ).group_by(func.date(Application.applied_at))
            
            result = await self.db.execute(stmt)
            rows = result.all()
            return {row.date.strftime('%Y-%m-%d'): row.count for row in rows}
        except (ImportError, AttributeError):
            return {}

    async def _get_daily_ai_interviews(self, user_id: int, start_date: datetime, end_date: datetime) -> dict[Any,
    Callable[..., int]] | dict[Any, Any]:
        """获取每日AI面试数"""
        try:
            from app.models import AIInterview
            stmt = select(
                func.date(AIInterview.started_at).label('date'),
                func.count().label('count')
            ).where(
                AIInterview.user_id == user_id,
                AIInterview.started_at >= start_date,
                AIInterview.started_at <= end_date
            ).group_by(func.date(AIInterview.started_at))
            
            result = await self.db.execute(stmt)
            rows = result.all()
            return {row.date.strftime('%Y-%m-%d'): row.count for row in rows}
        except (ImportError, AttributeError):
            return {}

    async def _get_daily_practices(self, user_id: int, start_date: datetime, end_date: datetime) -> dict[Any, Callable[
        ..., int]] | dict[Any, Any]:
        """获取每日刷题数"""
        try:
            from app.models import UserPractice
            stmt = select(
                func.date(UserPractice.practiced_at).label('date'),
                func.count().label('count')
            ).where(
                UserPractice.user_id == user_id,
                UserPractice.practiced_at >= start_date,
                UserPractice.practiced_at <= end_date
            ).group_by(func.date(UserPractice.practiced_at))
            
            result = await self.db.execute(stmt)
            rows = result.all()
            return {row.date.strftime('%Y-%m-%d'): row.count for row in rows}
        except (ImportError, AttributeError):
            return {}

    async def _get_daily_accuracy(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Optional[float]]:
        """获取每日正确率"""
        try:
            from app.models import UserPractice
            stmt = select(
                func.date(UserPractice.practiced_at).label('date'),
                func.sum(case((UserPractice.status == 'correct', 1), else_=0)).label('correct'),
                func.count().label('total')
            ).where(
                UserPractice.user_id == user_id,
                UserPractice.practiced_at >= start_date,
                UserPractice.practiced_at <= end_date
            ).group_by(func.date(UserPractice.practiced_at))
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            accuracy_dict = {}
            for row in rows:
                if row.total > 0:
                    accuracy_dict[row.date.strftime('%Y-%m-%d')] = round((row.correct / row.total) * 100, 2)
                else:
                    accuracy_dict[row.date.strftime('%Y-%m-%d')] = None
                    
            return accuracy_dict
        except (ImportError, AttributeError):
            return {}

    async def get_activities(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        获取个人最新动态
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            活动记录列表
        """
        activities = []
        
        # 1. 获取最近的投递记录
        activities.extend(await self._get_application_activities(user_id, limit))
        
        # 2. 获取最近的AI面试记录
        activities.extend(await self._get_ai_interview_activities(user_id, limit))
        
        # 3. 获取最近的刷题记录
        activities.extend(await self._get_practice_activities(user_id, limit))
        
        # 4. 获取最近的收藏记录
        activities.extend(await self._get_favorite_activities(user_id, limit))
        
        # 按时间倒序排序并截取
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        activities = activities[:limit]
        
        # 添加序号ID
        for idx, activity in enumerate(activities, 1):
            activity['id'] = idx
            
        return activities

    async def _get_application_activities(self, user_id: int, limit: int) -> List[Dict]:
        """获取投递活动"""
        try:
            from app.models import Application
            from app.models.job import Job
            
            stmt = select(Application, Job.title, Job.company_name).join(
                Job, Application.job_id == Job.id, isouter=True
            ).where(
                Application.user_id == user_id
            ).order_by(
                desc(Application.created_at)
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            activities = []
            for app, job_title, company_name in rows:
                display_company = company_name or app.company_name
                display_title = job_title or app.job_title
                
                activities.append({
                    "type": "application_created",
                    "title": "投递了新岗位",
                    "description": f"投递了 {display_company} - {display_title}",
                    "icon": "send",
                    "color": "blue",
                    "created_at": app.created_at
                })
            
            return activities
        except (ImportError, AttributeError):
            return []

    async def _get_ai_interview_activities(self, user_id: int, limit: int) -> List[Dict]:
        """获取AI面试活动"""
        try:
            from app.models import AIInterview
            
            stmt = select(AIInterview).where(
                AIInterview.user_id == user_id
            ).order_by(
                desc(AIInterview.started_at)
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            interviews = result.scalars().all()
            
            activities = []
            for interview in interviews:
                score_text = f"，得分{interview.overall_score}分" if interview.overall_score else ""
                activities.append({
                    "type": "ai_interview_completed",
                    "title": "完成AI面试",
                    "description": f"完成了 {interview.job_title or '模拟面试'}{score_text}",
                    "icon": "robot",
                    "color": "green",
                    "created_at": interview.ended_at or interview.started_at
                })
            
            return activities
        except (ImportError, AttributeError):
            return []

    async def _get_practice_activities(self, user_id: int, limit: int) -> List[Dict]:
        """获取刷题活动（聚合显示）"""
        try:
            from app.models import UserPractice
            from app.models import Question
            
            # 按天聚合刷题记录
            stmt = select(
                func.date(UserPractice.practiced_at).label('practice_date'),
                func.count().label('count'),
                func.sum(case((UserPractice.status == 'correct', 1), else_=0)).label('correct')
            ).where(
                UserPractice.user_id == user_id
            ).group_by(
                func.date(UserPractice.practiced_at)
            ).order_by(
                desc(func.date(UserPractice.practiced_at))
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            activities = []
            for row in rows:
                accuracy = round((row.correct / row.count) * 100, 1) if row.count > 0 else 0
                activities.append({
                    "type": "practice_session",
                    "title": "完成刷题练习",
                    "description": f"刷了{row.count}道题，正确率{accuracy}%",
                    "icon": "book",
                    "color": "purple",
                    "created_at": datetime.combine(row.practice_date, datetime.min.time())
                })
            
            return activities
        except (ImportError, AttributeError):
            return []

    async def _get_favorite_activities(self, user_id: int, limit: int) -> List[Dict]:
        """获取收藏活动"""
        try:
            from app.models.job import UserFavoriteJob, Job
            
            stmt = select(UserFavoriteJob, Job.title, Job.company_name).join(
                Job, UserFavoriteJob.job_id == Job.id
            ).where(
                UserFavoriteJob.user_id == user_id
            ).order_by(
                desc(UserFavoriteJob.created_at)
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            activities = []
            for fav, job_title, company_name in rows:
                activities.append({
                    "type": "job_favorited",
                    "title": "收藏了岗位",
                    "description": f"收藏了 {company_name} - {job_title}",
                    "icon": "star",
                    "color": "yellow",
                    "created_at": fav.created_at
                })
            
            return activities
        except (ImportError, AttributeError):
            return []
