"""Job lookup and formatting helpers shared by API, RAG, and agent tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.job import Job

MSG_JOBS_EMPTY = (
    "未找到匹配的岗位。可尝试放宽关键词或城市，"
    "或在「工作台 → 岗位」浏览全部岗位。"
)
MSG_RECOMMENDATIONS_EMPTY = (
    "暂未找到适合您的岗位推荐。请完善个人资料中的目标城市和学历，"
    "或在工作台浏览岗位。"
)
MSG_JOB_NOT_FOUND = "岗位不存在。请先用 search_jobs 获取有效的 [id=...] 后再调用匹配/优化工具。"

_EDUCATION_LABELS = {
    "unlimited": "不限",
    "junior_college": "大专",
    "bachelor": "本科",
    "master": "硕士",
    "doctor": "博士",
}


def format_education(value: str | None) -> str:
    if not value:
        return "不限"
    return _EDUCATION_LABELS.get(value, value)


def format_salary_range(job: Job) -> str:
    salary_display = getattr(job, "salary_display", None)
    if salary_display:
        return str(salary_display)
    if job.salary_min is not None and job.salary_max is not None:
        return f"{job.salary_min}-{job.salary_max}k"
    if job.salary_min is not None:
        return f"{job.salary_min}k起"
    if job.salary_max is not None:
        return f"最高{job.salary_max}k"
    return "面议"


def format_job_list_item(job: Job) -> str:
    """Single-line job summary for search/recommendation lists."""
    return (
        f"[id={job.id}] {job.title} @ {job.company_name} "
        f"| {job.city or '未知'} "
        f"| {format_salary_range(job)} "
        f"| {format_education(job.education_requirement)}"
    )


def format_job_list(jobs: list[Job], *, header: str | None = None) -> str:
    if not jobs:
        return MSG_JOBS_EMPTY
    lines: list[str] = []
    if header:
        lines.append(header)
    lines.extend(format_job_list_item(job) for job in jobs)
    lines.append("")
    lines.append("提示：调用 match_resume_to_job 或 optimize_for_job 时请使用上方的 [id=数字]。")
    return "\n".join(lines)


def _truncate(text: str | None, limit: int = 800) -> str:
    if not text:
        return "（暂无）"
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def format_job_detail(job: Job) -> str:
    """Multi-line job detail for get_job."""
    lines = [
        f"[id={job.id}] {job.title} @ {job.company_name}",
        f"城市：{job.city or '未知'}",
        f"薪资：{format_salary_range(job)}",
        f"学历：{format_education(job.education_requirement)}",
        f"经验：{getattr(job, 'experience_display', None) or '不限'}",
        "",
        "### 职位描述",
        _truncate(job.description),
        "",
        "### 岗位要求",
        _truncate(job.requirements),
        "",
        "提示：确认目标岗位后，可使用此 id 调用 match_resume_to_job 或 optimize_for_job。",
    ]
    return "\n".join(lines)


async def fetch_job(job_id: int):
    """Load a job by id via JobService."""
    from app.db.session import AsyncSessionLocal
    from app.services.job_service import JobService

    async with AsyncSessionLocal() as session:
        return await JobService(session).get_by_id(job_id)


def job_info_from_model(job) -> dict:
    """RAG optimize pipeline job payload."""
    return {
        "company_name": job.company_name,
        "title": job.title,
        "description": job.description or "",
        "requirements": job.requirements or "",
    }
