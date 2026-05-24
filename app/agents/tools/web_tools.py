"""Tavily web search tools for career content (not job listings)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from app.core.config import settings
from app.core.context import is_web_search_enabled

logger = logging.getLogger(__name__)

_tavily_client: TavilySearch | None = None

_QUERY_SUFFIX = {
    "industry": "行业趋势 就业市场 发展 2026",
    "interview": "面试技巧 面经 怎么准备 中国",
    "resume": "简历怎么写 简历优化 求职 中国",
}


def _get_tavily() -> TavilySearch | None:
    global _tavily_client
    if not settings.TAVILY_WEB_SEARCH_ENABLED:
        return None
    if not settings.TAVILY_API_KEY:
        return None
    if _tavily_client is None:
        _tavily_client = TavilySearch(
            max_results=settings.TAVILY_MAX_RESULTS,
            topic="general",
            tavily_api_key=settings.TAVILY_API_KEY,
        )
    return _tavily_client


def _build_query(query: str, category: str) -> str:
    q = (query or "").strip()
    suffix = _QUERY_SUFFIX.get(category, "")
    return f"{q} {suffix}".strip()


def _format_tavily_response(raw: Any, category_label: str) -> str:
    if raw is None:
        return f"未找到相关{category_label}（搜索无结果）"

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return f"未找到相关{category_label}（搜索无结果）"
        return f"[来源：互联网搜索 · {category_label}]\n\n{text}"

    if isinstance(raw, dict):
        if "error" in raw:
            return f"搜索暂时不可用：{raw.get('error')}"

        results = raw.get("results")
        if results is None and "answer" in raw:
            answer = (raw.get("answer") or "").strip()
            if answer:
                return f"[来源：互联网搜索 · {category_label}]\n\n{answer}"
            results = []

        if not results:
            return f"未找到相关{category_label}（搜索无结果）"

        lines = [f"[来源：互联网搜索 · {category_label}]"]
        for i, item in enumerate(results[: settings.TAVILY_MAX_RESULTS], 1):
            if not isinstance(item, dict):
                lines.append(f"{i}. {item}")
                continue
            title = item.get("title") or "无标题"
            url = item.get("url") or ""
            content = (item.get("content") or "").strip()
            block = f"{i}. {title}"
            if url:
                block += f"\n   链接：{url}"
            if content:
                block += f"\n   摘要：{content[:500]}"
            lines.append(block)
        return "\n\n".join(lines)

    return f"[来源：互联网搜索 · {category_label}]\n\n{json.dumps(raw, ensure_ascii=False)[:2000]}"


async def _tavily_search(query: str, category: str, category_label: str) -> str:
    if not is_web_search_enabled():
        return "用户未开启联网搜索，请仅使用知识库或平台内数据回答，并提示用户可在输入框开启「联网搜索」。"
    if not settings.TAVILY_WEB_SEARCH_ENABLED:
        return "互联网搜索未启用（TAVILY_WEB_SEARCH_ENABLED=false）"
    if not settings.TAVILY_API_KEY:
        return "互联网搜索未配置，请在 .env 中设置 TAVILY_API_KEY"

    client = _get_tavily()
    if client is None:
        return "互联网搜索初始化失败"

    full_query = _build_query(query, category)
    try:
        if hasattr(client, "ainvoke"):
            raw = await client.ainvoke(full_query)
        else:
            raw = await asyncio.to_thread(client.invoke, full_query)
    except Exception:
        logger.warning("Tavily search failed: category=%s query=%s", category, full_query[:80], exc_info=True)
        return f"搜索{category_label}时出错，请稍后重试"

    return _format_tavily_response(raw, category_label)


@tool
async def search_industry_news(query: str) -> str:
    """搜索行业资讯、技术趋势、就业市场动态等时效性信息。

    适用场景：
    - 「2026年前端发展趋势怎么样」
    - 「AI 行业最近有什么动态」
    - 「Java 就业市场好不好」

    不用于：搜索具体招聘岗位、公司内推、薪资精确统计（请用平台岗位工具或知识库）。"""
    return await _tavily_search(query, "industry", "行业资讯")


@tool
async def search_interview_tips(query: str) -> str:
    """搜索面试技巧、常见面试题、面试准备方法、面经经验。

    适用场景：
    - 「Java 后端面试一般问什么」
    - 「行为面试怎么准备」
    - 「自我介绍怎么说更好」

    平台知识库无结果或用户需要最新面经时优先使用。不用于搜索招聘岗位。"""
    return await _tavily_search(query, "interview", "面试技巧")


@tool
async def search_resume_writing_tips(query: str) -> str:
    """搜索简历撰写方法、简历优化技巧、项目经历描述、求职信写法。

    适用场景：
    - 「项目经历怎么写更有亮点」
    - 「应届生简历要注意什么」
    - 「如何把工作经历写进简历」

    用于通用写作方法论，不用于读取用户本人简历内容（请用 query_resume）。"""
    return await _tavily_search(query, "resume", "简历书写")
