"""Normalize assistant messages for UI display."""


def normalize_assistant_content(content: str) -> str:
    from app.agents.tools.resume_formatters import (
        looks_like_messy_resume_reply,
        normalize_structured_reply,
    )

    if looks_like_messy_resume_reply(content):
        return normalize_structured_reply(content)
    return content
