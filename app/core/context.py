"""Backward-compatible context helpers backed by RequestContext."""

from app.core.request_context import (
    RequestContext,
    get_request_context,
    new_trace_id,
    require_request_context,
    set_request_context,
    update_request_context,
)


def set_current_user_id(user_id: int):
    ctx = get_request_context()
    if ctx is None:
        set_request_context(
            RequestContext(user_id=user_id, trace_id=new_trace_id())
        )
    else:
        update_request_context(user_id=user_id)


def get_current_user_id() -> int:
    ctx = get_request_context()
    return ctx.user_id if ctx else 0


def require_current_user_id() -> int:
    return require_request_context().user_id


def set_trace_id(tid: str = "") -> str:
    tid = tid or new_trace_id()
    ctx = get_request_context()
    if ctx is None:
        set_request_context(RequestContext(user_id=0, trace_id=tid))
    else:
        update_request_context(trace_id=tid)
    return tid


def get_trace_id() -> str:
    ctx = get_request_context()
    return ctx.trace_id if ctx else ""


def set_conversation_thread_id(thread_id: str):
    ctx = get_request_context()
    if ctx is None:
        set_request_context(
            RequestContext(user_id=0, trace_id=new_trace_id(), thread_id=thread_id)
        )
    else:
        update_request_context(thread_id=thread_id)


def get_conversation_thread_id() -> str:
    ctx = get_request_context()
    return ctx.thread_id if ctx else ""
