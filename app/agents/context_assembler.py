"""Backward-compat shim — use app.agents.context instead."""

from app.agents.context.assembler import assemble_context, build_session_context, build_turn_context

__all__ = ["assemble_context", "build_session_context", "build_turn_context"]
