"""岗位相关工具 — 可被多个 agent 复用"""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from app.services.job_lookup import (
    MSG_JOBS_EMPTY,
    MSG_JOB_NOT_FOUND,
    MSG_RECOMMENDATIONS_EMPTY,
    fetch_job,
    format_job_detail,
    format_job_list,
)
from app.core.context import require_current_user_id
from app.schemas.job import JobSearchParams

_KNOWLEDGE_DOC_TYPES = frozenset({"job", "resume_guide", "interview"})


@tool
async def search_knowledge(query: str, doc_type: str = "job", limit: int = 5) -> str:
    """从知识库中检索信息。doc_type 可选值：job（岗位）、resume_guide（简历指导）、interview（面试）。
    当需要了解岗位内容、简历技巧、面试经验时使用此工具。"""
    if doc_type not in _KNOWLEDGE_DOC_TYPES:
        return (
            f"无效的 doc_type「{doc_type}」。"
            f"请使用：{', '.join(sorted(_KNOWLEDGE_DOC_TYPES))}"
        )

    from app.rag import get_knowledge_service

    results = await get_knowledge_service().search(query, limit, doc_type=doc_type)
    if not results:
        return (
            "知识库中未找到相关信息。"
            "可尝试换关键词，或使用联网搜索工具（若用户已开启）。"
        )

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
    """根据关键字、城市、薪资、学历等条件搜索平台内岗位。

    返回结果每行包含 [id=数字]，后续 match_resume_to_job / optimize_for_job 必须使用该 id。
    需要查看 JD 全文时，可先调用 get_job(job_id)。"""
    from app.db.session import AsyncSessionLocal
    from app.services.job_service import JobService

    user_id = require_current_user_id()
    params = JobSearchParams(
        keyword=keyword,
        city=city,
        salary_min=salary_min,
        education=education,
        page=1,
        page_size=10,
        sort_by="published_at",
        sort_order="desc",
    )

    async with AsyncSessionLocal() as session:
        total, jobs = await JobService(session).search(params, user_id=user_id)

    if not jobs:
        return MSG_JOBS_EMPTY

    header = f"共找到 {total} 个岗位，展示前 {len(jobs)} 个："
    return format_job_list(jobs, header=header)


@tool
async def get_job(job_id: int) -> str:
    """获取单个岗位的详细信息（JD、要求、薪资等）。

    在调用 match_resume_to_job 或 optimize_for_job 前，可用本工具确认目标岗位是否正确。
    job_id 来自 search_jobs 或 get_job_recommendations 返回的 [id=数字]。"""
    job = await fetch_job(job_id)
    if not job or not job.is_active:
        return MSG_JOB_NOT_FOUND
    return format_job_detail(job)


@tool
async def analyze_salary(job_title: str, city: Optional[str] = None) -> str:
    """分析指定岗位的薪资水平（基于平台内岗位样本）。"""
    from app.db.session import AsyncSessionLocal
    from app.models.job import Job
    from sqlalchemy import func, select

    async with AsyncSessionLocal() as session:
        stmt = select(
            func.avg(Job.salary_min),
            func.avg(Job.salary_max),
            func.min(Job.salary_min),
            func.max(Job.salary_max),
            func.count(Job.id),
        ).where(Job.title.contains(job_title), Job.is_active == True)
        if city:
            stmt = stmt.where(Job.city == city)
        result = (await session.execute(stmt)).one()
        avg_min, avg_max, min_sal, max_sal, count = result

    if not count:
        return (
            f"未找到岗位「{job_title}」的薪资数据。"
            "可尝试换关键词或城市，或使用 search_jobs 查看具体岗位。"
        )

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
    """根据用户画像（目标城市、学历等）获取个性化岗位推荐。

    返回结果包含 [id=数字]，可用于 get_job / match_resume_to_job / optimize_for_job。"""
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.services.job_service import JobService
    from sqlalchemy import select

    user_id = require_current_user_id()
    page_size = min(max(limit, 1), 10)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return "未找到用户信息，请重新登录后再试。"

        service = JobService(session)
        jobs = []
        header = f"为您推荐以下 {{count}} 个岗位："

        # 1) 目标城市 + 学历（最严格）
        if user.target_city or user.education:
            params = JobSearchParams(
                city=user.target_city,
                education=user.education,
                page=1,
                page_size=page_size,
                sort_by="published_at",
                sort_order="desc",
            )
            _, jobs = await service.search(params, user_id=user_id)

        # 2) 仅城市
        if not jobs and user.target_city:
            params = JobSearchParams(
                city=user.target_city,
                page=1,
                page_size=page_size,
                sort_by="published_at",
                sort_order="desc",
            )
            _, jobs = await service.search(params, user_id=user_id)
            header = "未找到与学历完全匹配的岗位，按目标城市为您推荐 {count} 个："

        # 3) 仅学历
        if not jobs and user.education:
            params = JobSearchParams(
                education=user.education,
                page=1,
                page_size=page_size,
                sort_by="published_at",
                sort_order="desc",
            )
            _, jobs = await service.search(params, user_id=user_id)
            header = "未找到目标城市岗位，按学历为您推荐 {count} 个："

        # 4) 热门岗位兜底
        if not jobs:
            jobs = await service.get_hot_jobs(limit=page_size)
            header = (
                "暂未找到与您资料匹配的岗位（请检查「设置 → 目标城市/学历」）。"
                "先为您展示平台热门岗位 {count} 个："
            )

    if not jobs:
        return MSG_RECOMMENDATIONS_EMPTY

    return format_job_list(jobs, header=header.format(count=len(jobs)))
