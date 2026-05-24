"""Background task helpers that preserve request context."""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine

from app.core.request_context import (
    RequestContext,
    copy_request_context,
    new_trace_id,
    run_with_request_context,
)


def create_context_task(
    coro: Coroutine[Any, Any, Any],
    *,
    name: str | None = None,
) -> asyncio.Task:
    """Schedule coroutine with a copy of the current RequestContext."""
    ctx = copy_request_context()
    if ctx is None:
        return asyncio.create_task(coro, name=name)
    return asyncio.create_task(
        run_with_request_context(coro, ctx),
        name=name,
    )


def create_background_task(
    coro: Coroutine[Any, Any, Any],
    *,
    user_id: int,
    thread_id: str = "",
    source: str = "background",
    trace_id: str | None = None,
    name: str | None = None,
) -> asyncio.Task:
    """Schedule coroutine with an explicit background RequestContext."""
    ctx = RequestContext(
        user_id=user_id,
        trace_id=trace_id or new_trace_id(),
        thread_id=thread_id,
        source=source,
    )
    return asyncio.create_task(
        run_with_request_context(coro, ctx),
        name=name,
    )
