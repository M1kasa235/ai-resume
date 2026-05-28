"""简历相关工具 — 包装 RAG 操作为 agent 可调用的工具"""

import logging

from langchain_core.tools import tool

from app.services.job_lookup import MSG_JOB_NOT_FOUND, fetch_job, job_info_from_model
from app.agents.tools.resume_formatters import (
    format_diagnosis_report,
    format_match_report,
    format_optimize_report,
    format_polish_report,
    format_query_report,
)
from app.core.context import require_current_user_id
from app.rag import get_rag_service

logger = logging.getLogger(__name__)


async def _run_rag(coro, formatter):
    """Run a RAG call and route exceptions through formatters."""
    try:
        result = await coro
        if isinstance(result, dict):
            return formatter(result)
        return formatter({"error": "工具返回格式异常，请稍后重试"})
    except Exception as exc:
        logger.warning("resume tool failed", exc_info=True)
        return formatter({"error": str(exc)})
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
    uid = require_current_user_id()
    return await _run_rag(
        get_rag_service().query(uid, question),
        format_query_report,
    )


@tool
async def diagnose_resume() -> str:
    """全面诊断简历，返回结构化分析结果（综合评分、优势列表、不足列表、逐项改进建议）。

适用场景（诊断型）：
- "分析一下我的简历" / "我的简历有什么问题" / "简历怎么样"
- "帮我看下简历有哪些不足"
- "简历哪里需要改进"

注意：本工具做的是简历本身质量的诊断，不涉及特定岗位的匹配度。"""
    uid = require_current_user_id()
    return await _run_rag(
        get_rag_service().diagnose(uid),
        format_diagnosis_report,
    )


@tool
async def optimize_for_job(job_id: int) -> str:
    """针对指定岗位优化简历，返回逐段原文与优化后的对比，以及完整优化版简历。

适用场景：
- "针对这个XX岗位帮我改简历"
- "帮我把简历改成适合投XX公司的"

前置条件：job_id 必须来自 search_jobs / get_job_recommendations 返回的 [id=数字]。
建议先 get_job(job_id) 确认岗位后再调用本工具。"""
    job = await fetch_job(job_id)
    if not job or not job.is_active:
        return MSG_JOB_NOT_FOUND

    uid = require_current_user_id()
    return await _run_rag(
        get_rag_service().optimize_for_job(uid, job_info_from_model(job)),
        format_optimize_report,
    )


@tool
async def match_resume_to_job(job_id: int) -> str:
    """分析简历与目标岗位的匹配度，返回各维度评分、整体匹配分、差距分析和投递建议。

适用场景：
- "我和这个岗位匹配吗？" / "这个岗位适合我吗？"
- "我投这个岗位有戏吗？"
- "对比一下我和这个岗位的差距"

前置条件：job_id 必须来自 search_jobs / get_job_recommendations 返回的 [id=数字]。
建议先 get_job(job_id) 确认岗位后再调用本工具。"""
    job = await fetch_job(job_id)
    if not job or not job.is_active:
        return MSG_JOB_NOT_FOUND

    uid = require_current_user_id()
    return await _run_rag(
        get_rag_service().match_job(uid, job),
        format_match_report,
    )


@tool
async def polish_section(section: str, content: str) -> str:
    """润色简历中的某段经历描述，使其更专业、更有说服力。不修改事实，只优化表达。

适用场景：
- "帮我把这段项目经历润色一下"
- "这段工作描述帮我写得更专业"
- "帮我优化这段自我评价"

参数：
- section: 段落类型，如 "项目经历"、"工作经历"、"自我评价"、"技能"
- content: **必填**，用户提供的待润色原文；不要留空或编造内容"""
    if not (content or "").strip():
        return "润色失败：请提供需要润色的原文 content（可直接粘贴简历段落）。"

    return await _run_rag(
        get_rag_service().polish(section, content),
        format_polish_report,
    )
