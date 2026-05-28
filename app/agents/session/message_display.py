"""Normalize stored messages for user-facing chat history."""

from __future__ import annotations

import re

_INJECTION_PREFIXES = (
    "[用户偏好：",
    "[系统上下文：",
    "[对话历史摘要]",
    "[今天是",
    "[还有",
    "请勿调用互联网",
)

_MEMORY_CATEGORY_PREFIXES = (
    "[技能事实:",
    "[偏好:",
    "[洞察:",
    "[目标:",
)


def is_injected_context_block(block: str) -> bool:
    text = block.strip()
    if not text:
        return True
    if any(text.startswith(prefix) for prefix in _INJECTION_PREFIXES):
        return True
    if any(text.startswith(prefix) for prefix in _MEMORY_CATEGORY_PREFIXES):
        return True
    if re.match(r"^\[还有\d+条候选记忆未注入\]$", text):
        return True
    return False


def normalize_user_message_for_display(content: str) -> str:
    """Strip assembled context so history shows only the user's original question."""
    text = (content or "").strip()
    if not text:
        return text

    if not any(marker in text for marker in (*_INJECTION_PREFIXES, *_MEMORY_CATEGORY_PREFIXES)):
        return text

    blocks = [part.strip() for part in re.split(r"\n\n+", text) if part.strip()]
    user_blocks = [block for block in blocks if not is_injected_context_block(block)]
    if user_blocks:
        return user_blocks[-1]
    return text
