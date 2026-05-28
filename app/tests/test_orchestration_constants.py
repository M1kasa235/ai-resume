"""Tests for supervisor routing constants."""

from app.agents.orchestration.constants import (
    is_resume_diagnose_intent,
    should_bypass_supervisor_for_resume,
)


def test_is_resume_diagnose_intent():
    assert is_resume_diagnose_intent("我的简历怎么样")
    assert is_resume_diagnose_intent("帮我分析简历")
    assert not is_resume_diagnose_intent("这个岗位和我匹配吗")
    assert not is_resume_diagnose_intent("")


def test_should_bypass_diagnose_keywords():
    assert should_bypass_supervisor_for_resume("简历有什么问题")


def test_should_bypass_structured_resume_query():
    assert should_bypass_supervisor_for_resume("帮我看看简历有哪些不足")


def test_should_not_bypass_cross_domain():
    assert not should_bypass_supervisor_for_resume("针对这个前端岗位优化简历")
