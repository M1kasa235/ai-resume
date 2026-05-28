"""LangGraph run config shared by supervisor and sub-agents."""

from __future__ import annotations

from app.core.config import settings


def agent_run_config(thread_id: str, *, recursion_limit: int | None = None) -> dict:
    """Build RunnableConfig for agent ainvoke/astream calls."""
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit or settings.AGENT_RECURSION_LIMIT,
    }
