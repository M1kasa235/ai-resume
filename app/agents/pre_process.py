"""Backward-compat facade — delegates to app.agents.context."""

import time
import logging

from app.core.context import get_trace_id
from app.agents.context.intent import classify_intent
from app.agents.context.assembler import assemble_context

logger = logging.getLogger(__name__)

# Re-export for legacy imports
from app.agents.context.compression import COMPRESSION_PROMPT, COMPRESSION_THRESHOLD  # noqa: F401

__all__ = [
    "classify_intent",
    "assemble_context",
    "pre_process",
    "COMPRESSION_PROMPT",
    "COMPRESSION_THRESHOLD",
]


async def pre_process(user_id: int, thread_id: str, message: str) -> str:
    """预处理用户消息，返回 enriched prompt（兼容旧接口）。"""
    t0 = time.time()
    bundle = await assemble_context(user_id, thread_id, message)
    enriched = bundle.render()
    meta = bundle.to_log_dict()
    elapsed = int((time.time() - t0) * 1000)
    logger.info(
        "[trace=%s] pre_process done %sms intent=%s blocks=%s truncated=%s",
        get_trace_id(),
        elapsed,
        meta.get("intent"),
        len(meta.get("blocks", [])),
        meta.get("truncated"),
    )
    return enriched
