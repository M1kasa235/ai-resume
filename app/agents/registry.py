"""AgentRegistry — lazy agent cache and role-based dispatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

logger = __import__("logging").getLogger(__name__)


class AgentRegistry:
    """Central registry for agent instances and sub-agent role dispatch."""

    _agents: dict[str, Any] = {}
    _role_getters: dict[str, Callable[[], Any]] = {}

    @classmethod
    def get_or_create(cls, name: str, factory: Callable[[], Any]) -> Any:
        if name not in cls._agents:
            cls._agents[name] = factory()
        return cls._agents[name]

    @classmethod
    def register_role(cls, role: str, getter: Callable[[], Any]) -> None:
        cls._role_getters[role] = getter

    @classmethod
    def get_agent_for_role(cls, role: str) -> Any:
        getter = cls._role_getters.get(role)
        if getter is None:
            raise ValueError(f"Unknown agent role: {role}")
        return getter()

    @classmethod
    def registered_roles(cls) -> tuple[str, ...]:
        return tuple(cls._role_getters.keys())

    @classmethod
    def clear(cls, name: str = ""):
        """Clear cached agents (tests)."""
        if name:
            cls._agents.pop(name, None)
        else:
            cls._agents.clear()
            cls._role_getters.clear()
