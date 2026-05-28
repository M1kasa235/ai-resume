"""Career advisor agent factory."""

from app.agents.factories.base import lazy_agent_getter
from app.agents.prompts.career import CAREER_SYSTEM_PROMPT
from app.agents.registry import AgentRegistry
from app.agents.tools.collections import CAREER_TOOLS

get_career_agent = lazy_agent_getter(
    "career",
    tools=CAREER_TOOLS,
    system_prompt=CAREER_SYSTEM_PROMPT,
    name="career-advisor",
    progress=True,
)

AgentRegistry.register_role("career", get_career_agent)
