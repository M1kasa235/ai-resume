"""Backward-compat shim — use app.agents.context instead."""

from app.agents.context.budget import apply_budget, strip_api_date_prefix

__all__ = ["apply_budget", "strip_api_date_prefix"]
