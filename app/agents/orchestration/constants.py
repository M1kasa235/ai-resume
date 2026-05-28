"""Routing heuristics for supervisor bypass (no protocol constants here)."""

from app.agents.common.protocol import PASSTHROUGH_END, PASSTHROUGH_START, SUB_AGENT_TIMEOUT

STRUCTURED_KEYWORDS = [
    "诊断", "优化", "匹配", "评分", "修改简历", "改简历", "润色",
    "怎么样", "改进", "看看", "分析", "有什么问题", "有哪些不足",
]

RESUME_MARKERS = ("简历", "履历", "CV", "cv")

RESUME_DIAGNOSE_KEYWORDS = (
    "简历怎么样",
    "简历如何",
    "帮我分析简历",
    "分析我的简历",
    "诊断简历",
    "简历诊断",
    "简历有什么问题",
    "简历问题",
    "看看我的简历",
    "评估简历",
    "简历评分",
    "简历打分",
)

RESUME_DIAGNOSE_EXCLUDE = (
    "岗位",
    "职位",
    "匹配",
    "优化这段",
    "润色",
    "改写",
    "针对",
    "薪资",
    "面试",
)


def is_structured_query(query: str) -> bool:
    return any(kw in query for kw in STRUCTURED_KEYWORDS)


def is_resume_diagnose_intent(query: str) -> bool:
    """True when the user likely wants a full resume diagnosis (supervisor bypass)."""
    text = (query or "").strip()
    if not text:
        return False
    return any(k in text for k in RESUME_DIAGNOSE_KEYWORDS)


def should_bypass_supervisor_for_resume(query: str) -> bool:
    """纯简历结构化请求直接走 resume 专家，避免 supervisor 二次总结。"""
    text = (query or "").strip()
    if not text:
        return False
    if any(k in text for k in RESUME_DIAGNOSE_EXCLUDE):
        return False
    if is_resume_diagnose_intent(query):
        return True
    if not is_structured_query(query):
        return False
    return any(marker in query for marker in RESUME_MARKERS)


__all__ = [
    "PASSTHROUGH_END",
    "PASSTHROUGH_START",
    "SUB_AGENT_TIMEOUT",
    "is_resume_diagnose_intent",
    "is_structured_query",
    "should_bypass_supervisor_for_resume",
]
