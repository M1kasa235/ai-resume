"""Shared agent factory helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.registry import AgentRegistry

ModelFactory: TypeAlias = Callable[[], BaseChatModel]


def build_agent(
    *,
    model: BaseChatModel,
    tools: Sequence[BaseTool | Callable[..., Any]],
    system_prompt: str,
    name: str,
    progress: bool = False,
) -> Any:
    """Instantiate a LangChain agent (no registry)."""
    from app.agents.config import create_checkpointer, make_middleware

    return create_agent(
        model=model,
        tools=list(tools),
        system_prompt=system_prompt,
        name=name,
        checkpointer=create_checkpointer(),
        middleware=make_middleware(model, progress=progress),
    )


def lazy_agent_getter(
    registry_key: str,
    *,
    tools: Sequence[BaseTool | Callable[..., Any]],
    system_prompt: str,
    name: str,
    progress: bool = False,
    model_factory: ModelFactory | None = None,
) -> Callable[[], Any]:
    """Return a lazy loader registered in AgentRegistry."""

    def get_agent() -> Any:
        def _build() -> Any:
            from app.core.llm import get_chat_model

            model = (model_factory or get_chat_model)()
            return build_agent(
                model=model,
                tools=tools,
                system_prompt=system_prompt,
                name=name,
                progress=progress,
            )

        return AgentRegistry.get_or_create(registry_key, _build)

    return get_agent
