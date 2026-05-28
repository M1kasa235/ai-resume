"""Backward-compat re-exports — use app.agents.common.streaming."""

from app.agents.common.progress import (
    STATUS_ASSEMBLE_CONTEXT,
    STATUS_COORDINATE,
    STATUS_GENERATE,
    STATUS_RESUME_DIAGNOSE,
    STATUS_UNDERSTAND,
    tool_status_message,
)
from app.agents.common.streaming import (
    STREAM_CHUNK_SIZE,
    extract_custom_event,
    extract_stream_text,
    iter_text_chunks,
    sse_event,
)

__all__ = [
    "STATUS_ASSEMBLE_CONTEXT",
    "STATUS_COORDINATE",
    "STATUS_GENERATE",
    "STATUS_RESUME_DIAGNOSE",
    "STATUS_UNDERSTAND",
    "STREAM_CHUNK_SIZE",
    "sse_event",
    "tool_status_message",
    "iter_text_chunks",
    "extract_stream_text",
    "extract_custom_event",
]
