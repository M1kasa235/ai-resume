"""Backward-compat shim — use app.agents.context instead."""

from app.agents.context.bundle import ContextBlock, ContextBundle

__all__ = ["ContextBlock", "ContextBundle"]
