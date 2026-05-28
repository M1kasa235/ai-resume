"""Tests for chat message display normalization."""

from app.agents.session.message_display import normalize_user_message_for_display

ENRICHED = """[用户偏好：已关闭联网搜索]
请勿调用互联网搜索工具；请使用 search_knowledge 与平台内岗位数据。

[系统上下文：今天是 2026-05-24]

[对话历史摘要] 用户彭安旭求职 AI 应用开发实习。

我现在更新了简历，你帮我看看怎么样，有哪些地方需要改进"""


def test_strip_enriched_user_message():
    result = normalize_user_message_for_display(ENRICHED)
    assert result == "我现在更新了简历，你帮我看看怎么样，有哪些地方需要改进"


def test_plain_message_unchanged():
    plain = "帮我推荐前端实习岗位"
    assert normalize_user_message_for_display(plain) == plain
