"""岗位相关工具 — 可被多个 agent 复用"""

from typing import Optional
from langchain_core.tools import tool
from app.core.context import require_current_user_id


@tool
async def search_knowledge(query: str, doc_type: str = "job", limit: int = 5) -> str:
    """从知识库中检索信息。doc_type 可选值：job（岗位）、resume_guide（简历指导）、interview（面试）。
    当需要了解岗位内容、简历技巧、面试经验时使用此工具。"""
    from app.rag import get_knowledge_service

    results = await get_knowledge_service().search(query, limit, doc_type=doc_type)
    if not results:
        return "知识库中未找到相关信息"

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "未知"
        category = r.get("category") or ""
        content = r.get("content") or ""
        header = f"【{title}】" + (f" [{category}]" if category else "")
        lines.append(f"{i}. {header}\n{content}\n")
    return "\n---\n".join(lines)


@tool
async def search_jobs(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    salary_min: Optional[int] = None,
    education: Optional[str] = None,
) -> str:
    """根据关键字、城市、薪资等条件搜索匹配的岗位"""
    from app.db.session import AsyncSessionLocal
    from app.models.job import Job
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        stmt = select(Job).where(Job.is_active == True)
        if keyword:
            stmt = stmt.where(Job.title.ilike(f"%{keyword}%"))
        if city:
            stmt = stmt.where(Job.city.ilike(f"%{city}%"))
        if salary_min:
            stmt = stmt.where(Job.salary_max >= salary_min)
        if education:
            stmt = stmt.where(Job.education_requirement == education)
        stmt = stmt.limit(10)
        results = (await session.execute(stmt)).scalars().all()
        if not results:
            return "未找到匹配的岗位"
        lines = []
        for j in results:
            lines.append(f"- {j.title} @ {j.company_name} | {j.city} | {j.salary_min}-{j.salary_max}k | {j.education_requirement or '不限'}")
        return "\n".join(lines)


@tool
async def analyze_salary(job_title: str, city: Optional[str] = None) -> str:
    """分析指定岗位的薪资水平"""
    from app.db.session import AsyncSessionLocal
    from app.models.job import Job
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        stmt = select(
            func.avg(Job.salary_min), func.avg(Job.salary_max),
            func.min(Job.salary_min), func.max(Job.salary_max),
            func.count(Job.id),
        ).where(Job.title.ilike(f"%{job_title}%"))
        if city:
            stmt = stmt.where(Job.city.ilike(f"%{city}%"))
        result = (await session.execute(stmt)).one()
        avg_min, avg_max, min_sal, max_sal, count = result
        if not count:
            return f"未找到岗位「{job_title}」的薪资数据"
        return (
            f"岗位：{job_title}\n"
            f"样本数：{count}\n"
            f"平均薪资范围：{avg_min:.0f}-{avg_max:.0f}k\n"
            f"最低薪资：{min_sal:.0f}k\n"
            f"最高薪资：{max_sal:.0f}k\n"
            f"{'城市：' + city if city else '全国范围'}"
        )


@tool
async def get_job_recommendations(limit: int = 5) -> str:
    """根据用户画像获取个性化岗位推荐"""
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.job import Job
    from sqlalchemy import select, or_

    user_id = require_current_user_id()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return "未找到用户信息"

        stmt = select(Job).where(Job.is_active == True)
        conditions = []
        if user.target_city:
            conditions.append(Job.city.ilike(f"%{user.target_city}%"))
        if user.education:
            conditions.append(Job.education_requirement == user.education)
        if conditions:
            stmt = stmt.where(or_(*conditions))
        stmt = stmt.order_by(Job.created_at.desc()).limit(limit)
        results = (await session.execute(stmt)).scalars().all()
        if not results:
            return "暂未找到适合您的岗位推荐"
        lines = [f"为您推荐以下{len(results)}个岗位："]
        for j in results:
            match = []
            if user.target_city and j.city and user.target_city in j.city:
                match.append("城市匹配")
            match.append("薪资透明")
            lines.append(f"- {j.title} @ {j.company_name} | {j.city} | {j.salary_min}-{j.salary_max}k | 匹配: {'/'.join(match)}")
        return "\n".join(lines)
