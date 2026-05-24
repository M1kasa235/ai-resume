"""Backward-compat shim — use app.agents.context instead."""

from app.agents.context.threads import build_sub_agent_thread, list_related_threads

__all__ = ["build_sub_agent_thread", "list_related_threads"]
