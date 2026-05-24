"""Backward-compat shim — use app.agents.memory.ingest."""

from app.agents.memory.ingest import run_memory_agent, set_memory_source

__all__ = ["run_memory_agent", "set_memory_source"]
