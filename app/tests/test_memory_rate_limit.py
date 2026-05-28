"""Tests for memory LLM rate limiting."""

import pytest
from fastapi import HTTPException

from app.core.limiter import _simple, check_memory_llm_quota


@pytest.fixture(autouse=True)
def _reset_limiter(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.REDIS_RATE_LIMIT_ENABLED", False)
    _simple.requests.clear()
    yield
    _simple.requests.clear()


@pytest.mark.asyncio
async def test_memory_llm_quota_allows_under_limit(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.MEMORY_LLM_RATE_LIMIT_PER_MINUTE", 3)
    await check_memory_llm_quota(42)
    await check_memory_llm_quota(42)
    await check_memory_llm_quota(42)


@pytest.mark.asyncio
async def test_memory_llm_quota_blocks_over_limit(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.MEMORY_LLM_RATE_LIMIT_PER_MINUTE", 2)
    await check_memory_llm_quota(99)
    await check_memory_llm_quota(99)
    with pytest.raises(HTTPException) as exc:
        await check_memory_llm_quota(99)
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_memory_llm_quota_isolated_per_user(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.MEMORY_LLM_RATE_LIMIT_PER_MINUTE", 1)
    await check_memory_llm_quota(1)
    await check_memory_llm_quota(2)
