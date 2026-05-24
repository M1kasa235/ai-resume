"""Unified request-scoped context for agent/tool chains."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, replace
from typing import Any, Coroutine
from uuid import uuid4

_request_context: contextvars.ContextVar[RequestContext | None] = contextvars.ContextVar(
    "request_context", default=None
)


@dataclass(frozen=True)
class RequestContext:
    user_id: int
    trace_id: str
    thread_id: str = ""
    source: str = "api"
    route: str = ""


def set_request_context(ctx: RequestContext) -> RequestContext:
    _request_context.set(ctx)
    return ctx


def get_request_context() -> RequestContext | None:
    return _request_context.get()


def require_request_context() -> RequestContext:
    ctx = _request_context.get()
    if ctx is None or ctx.user_id <= 0:
        raise RuntimeError("request context is not set or user_id is missing")
    return ctx


def update_request_context(**kwargs: Any) -> RequestContext:
    current = _request_context.get()
    if current is None:
        current = RequestContext(user_id=0, trace_id=new_trace_id())
    updated = replace(current, **kwargs)
    _request_context.set(updated)
    return updated


def new_trace_id() -> str:
    return str(uuid4())[:8]


def copy_request_context() -> RequestContext | None:
    return _request_context.get()


async def run_with_request_context(coro: Coroutine[Any, Any, Any], ctx: RequestContext):
    set_request_context(ctx)
    return await coro
