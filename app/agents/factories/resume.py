"""Resume assistant agent factory."""

from app.agents.factories.base import lazy_agent_getter
from app.agents.prompts.resume import RESUME_SYSTEM_PROMPT
from app.agents.registry import AgentRegistry
from app.agents.tools.collections import RESUME_TOOLS
from app.core.llm import get_structured_model

get_resume_agent = lazy_agent_getter(
    "resume",
    tools=RESUME_TOOLS,
    system_prompt=RESUME_SYSTEM_PROMPT,
    name="resume-assistant",
    progress=True,
    model_factory=get_structured_model,
)

AgentRegistry.register_role("resume", get_resume_agent)
