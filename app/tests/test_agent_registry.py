"""Tests for AgentRegistry role dispatch."""

import pytest

from app.agents.registry import AgentRegistry


@pytest.fixture(autouse=True)
def _reset_registry():
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


def test_register_and_get_role():
    calls = []

    def getter():
        calls.append(1)
        return object()

    AgentRegistry.register_role("test", getter)
    AgentRegistry.get_agent_for_role("test")
    AgentRegistry.get_agent_for_role("test")
    assert len(calls) == 2


def test_unknown_role_raises():
    with pytest.raises(ValueError, match="Unknown agent role"):
        AgentRegistry.get_agent_for_role("missing")
