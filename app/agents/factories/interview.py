"""Interview agent factory."""

from app.agents.factories.base import lazy_agent_getter
from app.agents.prompts.interview import INTERVIEW_SYSTEM_PROMPT
from app.agents.registry import AgentRegistry
from app.agents.tools.collections import INTERVIEW_TOOLS

get_interview_agent = lazy_agent_getter(
    "interview",
    tools=INTERVIEW_TOOLS,
    system_prompt=INTERVIEW_SYSTEM_PROMPT,
    name="interviewer",
)

AgentRegistry.register_role("interview", get_interview_agent)
