"""简历相关工具 — 包装 RAG 操作为 agent 可调用的工具"""

import json
import logging
from langchain_core.tools import tool
from app.rag import get_rag_service
from app.core.context import get_current_user_id

logger = logging.getLogger(__name__)


@tool
async def query_resume(question: str) -> str:
    """基于简历内容回答问题。用于查询简历中的具体事实信息。

适用场景（查询型）：
- "我的项目经验有哪些？" / "我掌握哪些技能？"
- "简历里有没有提到 Python？"
- "我上一份工作是什么？"

不适用场景：
- 要评分/分析/建议 → 用 diagnose_resume
- 要针对岗位改简历 → 用 optimize_for_job
- 要看匹配度 → 用 match_resume_to_job"""
    result = await get_rag_service().query(get_current_user_id(), question)
    return json.dumps(result, ensure_ascii=False)


@tool
async def diagnose_resume() -> str:
    """全面诊断简历，返回结构化分析结果（综合评分、优势列表、不足列表、逐项改进建议）。

适用场景（诊断型）：
- "分析一下我的简历" / "我的简历有什么问题" / "简历怎么样"
- "帮我看下简历有哪些不足"
- "简历哪里需要改进"

注意：本工具做的是简历本身质量的诊断，不涉及特定岗位的匹配度。"""
    result = await get_rag_service().diagnose(get_current_user_id())
    return json.dumps(result, ensure_ascii=False)


@tool
async def optimize_for_job(job_id: int) -> str:
    """针对指定岗位优化简历，返回逐段原文与优化后的对比，以及完整优化版简历。

适用场景：
- "针对这个XX岗位帮我改简历"
- "帮我把简历改成适合投XX公司的"

注意：需要提供 job_id，先用 search_jobs 找到目标岗位再调用本工具。"""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.job import Job

    async with AsyncSessionLocal() as session:
        stmt = select(Job).where(Job.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            return "岗位不存在"

    job_info = {
        "company_name": job.company_name,
        "title": job.title,
        "description": job.description or "",
        "requirements": job.requirements or "",
    }
    result = await get_rag_service().optimize_for_job(get_current_user_id(), job_info)
    return json.dumps(result, ensure_ascii=False)


@tool
async def match_resume_to_job(job_id: int) -> str:
    """分析简历与目标岗位的匹配度，返回各维度评分（技能/经验/学历等）、整体匹配分、差距分析和投递建议。

适用场景：
- "我和这个岗位匹配吗？" / "这个岗位适合我吗？"
- "我投这个岗位有戏吗？"
- "对比一下我和这个岗位的差距"

注意：需要提供 job_id，先用 search_jobs 找到目标岗位再调用本工具。"""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.job import Job

    async with AsyncSessionLocal() as session:
        stmt = select(Job).where(Job.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            return "岗位不存在"

    result = await get_rag_service().match_job(get_current_user_id(), job)
    return json.dumps(result, ensure_ascii=False)


@tool
async def polish_section(section: str, content: str) -> str:
    """润色简历中的某段经历描述，使其更专业、更有说服力。不修改事实，只优化表达。

适用场景：
- "帮我把这段项目经历润色一下"
- "这段工作描述帮我写得更专业"
- "帮我优化这段自我评价"

参数：
- section: 段落类型，如 "项目经历"、"工作经历"、"自我评价"、"技能" 等
- content: 需要润色的原文内容"""
    result = await get_rag_service().polish(section, content)
    return json.dumps(result, ensure_ascii=False)
