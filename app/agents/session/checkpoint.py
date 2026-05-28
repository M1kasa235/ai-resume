"""Checkpoint helpers for LangGraph thread state."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


async def checkpoint_transcript(
    thread_id: str,
    *,
    max_messages: int = 20,
    tail_messages: int | None = None,
) -> str:
    """Read recent message text from a checkpoint thread (for memory triggers)."""
    from app.agents.config import create_checkpointer

    checkpoint = await create_checkpointer().aget({"configurable": {"thread_id": thread_id}})
    if not checkpoint or not checkpoint.get("channel_values"):
        return ""

    messages = checkpoint["channel_values"].get("messages", [])
    contents = [
        m.content
        for m in messages[-max_messages:]
        if hasattr(m, "content") and m.content
    ]
    if tail_messages is not None and tail_messages > 0:
        contents = contents[-tail_messages:]
    return "\n".join(str(c) for c in contents)


async def replace_last_human_message(
    agent: Any,
    thread_id: str,
    plain: str,
    *,
    timeout: float = 15,
) -> None:
    """Replace the last stored HumanMessage content (e.g. enriched → raw prompt)."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    messages = list(state.values.get("messages", []))
    last_human = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human = msg
            break
    if last_human is None or last_human.content == plain:
        return
    await asyncio.wait_for(
        agent.aupdate_state(
            config,
            {"messages": [HumanMessage(content=plain, id=last_human.id)]},
        ),
        timeout=timeout,
    )


async def append_thread_messages(
    agent: Any,
    thread_id: str,
    messages: list,
    *,
    timeout: float = 15,
) -> None:
    """Append messages to a thread checkpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    await asyncio.wait_for(
        agent.aupdate_state(config, {"messages": messages}),
        timeout=timeout,
    )
