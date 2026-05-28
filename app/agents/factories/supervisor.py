"""Supervisor agent factory."""

from app.agents.factories.base import lazy_agent_getter
from app.agents.prompts.supervisor import SUPERVISOR_PROMPT
from app.agents.registry import AgentRegistry
from app.agents.tools.supervisor_tools import SUPERVISOR_TOOLS

get_supervisor = lazy_agent_getter(
    "supervisor",
    tools=SUPERVISOR_TOOLS,
    system_prompt=SUPERVISOR_PROMPT,
    name="supervisor",
    progress=True,
)

AgentRegistry.register_role("supervisor", get_supervisor)
