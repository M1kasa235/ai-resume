"""Composable system-prompt blocks shared across agents."""

from __future__ import annotations

from app.agents.context.temporal import TEMPORAL_REASONING_RULES
from app.agents.common.protocol import PASSTHROUGH_END, PASSTHROUGH_START


def temporal_context_block() -> str:
    return (
        "## 系统上下文\n\n"
        "每条用户消息前可能会附带 `[系统上下文：今天是 YYYY-MM-DD]`，"
        "请**仅使用该日期**作为「今天」，不要使用训练数据中的默认年份。\n\n"
        f"{TEMPORAL_REASONING_RULES}"
    )


def web_search_preference_block(enabled: bool) -> str:
    if enabled:
        return (
            "[用户偏好：已开启联网搜索]\n"
            "行业资讯、面试技巧、简历书写类问题可调用 search_industry_news、"
            "search_interview_tips、search_resume_writing_tips。"
        )
    return (
        "[用户偏好：已关闭联网搜索]\n"
        "请勿调用互联网搜索工具；请使用 search_knowledge 与平台内岗位数据。"
    )


def web_search_routing_note() -> str:
    return (
        "关键：遵守消息中的「用户偏好：已开启/关闭联网搜索」；"
        "关闭时不要调用互联网搜索工具。"
    )


def json_output_guardrails() -> str:
    return (
        "## 严格禁止\n"
        "- 禁止输出 JSON、字典、列表等原始数据结构\n"
        "- 禁止重复「请稍等」等客套话；调用工具后直接呈现报告\n"
        "- 禁止生成假设的简历片段、示例简历或虚构信息\n"
        "- 禁止为工具返回的真实数据添加虚构信息（姓名、公司名、学历等）\n"
        "- 如果工具返回的内容不足以回答用户问题，直接告知用户，不要自行补充"
    )


def supervisor_passthrough_rules() -> str:
    return (
        "### 结构化结果 → 原样透传\n"
        f"如果简历专家返回的内容被 `{PASSTHROUGH_START}` 和 `{PASSTHROUGH_END}` 包裹，"
        "你必须**原样输出**标记内的 Markdown 报告（去掉标记符号），"
        "**不要**再加开场白或重复总结。"
    )
