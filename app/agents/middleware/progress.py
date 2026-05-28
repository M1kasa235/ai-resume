"""Emit agent lifecycle steps via runtime.stream_writer for chat streaming UI."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState, ContextT, ResponseT
from langchain_core.messages import ToolMessage

from app.agents.common.progress import STATUS_GENERATE, tool_status_message

if TYPE_CHECKING:
    from langgraph.types import Command

    from langchain.agents.middleware.types import ToolCallRequest


class AgentProgressMiddleware(AgentMiddleware[AgentState[ResponseT], ContextT, ResponseT]):
    """Push tool/model milestones to runtime.stream_writer (surfaces as on_custom_event)."""

    async def abefore_model(self, state: AgentState[ResponseT], runtime) -> dict[str, Any] | None:
        runtime.stream_writer({"type": "status", "message": STATUS_GENERATE, "step": "generate"})
        return None

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool.name if request.tool else request.tool_call["name"]
        runtime: Any = request.runtime
        runtime.stream_writer(
            {"type": "status", "message": tool_status_message(tool_name), "step": f"tool:{tool_name}"}
        )
        return await handler(request)
