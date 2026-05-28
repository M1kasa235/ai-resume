"""Agent factories and registry bootstrap."""

from app.agents.factories.career import get_career_agent
from app.agents.factories.interview import get_interview_agent
from app.agents.factories.resume import get_resume_agent
from app.agents.factories.supervisor import get_supervisor


def bootstrap_agent_registry() -> None:
    """Import all factories so AgentRegistry role bindings are registered."""
    _ = (get_career_agent, get_resume_agent, get_interview_agent, get_supervisor)


__all__ = [
    "bootstrap_agent_registry",
    "get_career_agent",
    "get_interview_agent",
    "get_resume_agent",
    "get_supervisor",
]
