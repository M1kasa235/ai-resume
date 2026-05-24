"""Layered context models: Session / Turn / Tool."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionContext:
    user_id: int
    memory_count: int = 0


@dataclass
class TurnContext:
    thread_id: str
    raw_message: str
    intent: dict = field(default_factory=dict)
    history_summary: str = ""
    memory_text: str = ""
    memory_selected: list[dict] = field(default_factory=list)
    system_date: str = ""


@dataclass
class ToolContext:
    trace_id: str
    source: str
    parent_thread_id: str
    sub_agent_thread_id: str = ""
