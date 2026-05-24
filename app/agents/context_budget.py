"""Context budget policies for prompt assembly."""

from __future__ import annotations

import re

from app.agents.context_bundle import ContextBlock, ContextBundle
from app.agents.context_layers import TurnContext
from app.core.config import settings

_DATE_PREFIX_RE = re.compile(
    r"^\[今天是\s*\d{4}-\d{2}-\d{2}\]\s*\n?",
    re.MULTILINE,
)


def strip_api_date_prefix(message: str) -> str:
    if not settings.CONTEXT_STRIP_API_DATE_PREFIX:
        return message.strip()
    return _DATE_PREFIX_RE.sub("", message.strip(), count=1).strip()


def apply_budget(turn: TurnContext) -> ContextBundle:
    blocks: list[ContextBlock] = []

    if turn.system_date:
        blocks.append(
            ContextBlock(
                kind="system",
                content=f"[系统上下文：今天是 {turn.system_date}]",
                priority=1,
                char_budget=settings.CONTEXT_SYSTEM_MAX_CHARS,
            )
        )

    if turn.memory_text and turn.intent.get("needs_memory"):
        blocks.append(
            ContextBlock(
                kind="memory",
                content=turn.memory_text,
                priority=2,
                char_budget=settings.CONTEXT_MEMORY_MAX_CHARS,
            )
        )

    if turn.history_summary:
        blocks.append(
            ContextBlock(
                kind="history",
                content=turn.history_summary,
                priority=3,
                char_budget=settings.CONTEXT_HISTORY_MAX_CHARS,
            )
        )

    blocks.append(
        ContextBlock(
            kind="user",
            content=turn.raw_message,
            priority=1,
            char_budget=settings.CONTEXT_USER_MAX_CHARS,
        )
    )

    selected: list[ContextBlock] = []
    truncated = 0
    used = 0
    total_budget = settings.CONTEXT_TOTAL_MAX_CHARS

    for block in sorted(blocks, key=lambda b: b.priority):
        if not block.content:
            continue
        budget = block.char_budget or total_budget
        remaining = max(0, total_budget - used)
        allowance = min(budget, remaining)
        if allowance <= 0:
            truncated += 1
            continue
        content = block.content
        if len(content) > allowance:
            content = content[:allowance]
            truncated += 1
        selected.append(
            ContextBlock(
                kind=block.kind,
                content=content,
                priority=block.priority,
                char_budget=block.char_budget,
            )
        )
        used += len(content)

    # Restore human-readable order after priority selection.
    order = {"system": 0, "memory": 1, "history": 2, "user": 3}
    selected.sort(key=lambda b: order.get(b.kind, 99))

    return ContextBundle(
        blocks=selected,
        meta={
            "intent": turn.intent.get("category"),
            "truncated_blocks": truncated,
            "memory_items": len(turn.memory_selected),
            "history_len": len(turn.history_summary or ""),
        },
    )
