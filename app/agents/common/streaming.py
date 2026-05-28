"""SSE and token-stream helpers for agent responses."""

from __future__ import annotations

import json
from typing import Any

STREAM_CHUNK_SIZE = 64


def sse_event(event_type: str, **payload: Any) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def iter_text_chunks(text: str, chunk_size: int = STREAM_CHUNK_SIZE):
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]


def extract_stream_text(chunk) -> str:
    """Normalize token chunks from astream_events into plain text."""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return ""


def extract_custom_event(event: dict) -> dict | None:
    """Extract payload from an on_custom_event emitted by runtime.stream_writer."""
    if event.get("event") != "on_custom_event":
        return None
    return event.get("data", {})
