"""请求级上下文 — 通过 contextvars 在 agent/tool 链中传递 user_id 和 trace_id"""

import contextvars
from uuid import uuid4

_current_user_id: contextvars.ContextVar[int] = contextvars.ContextVar(
    "current_user_id", default=0
)

_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)


def set_current_user_id(user_id: int):
    _current_user_id.set(user_id)


def get_current_user_id() -> int:
    return _current_user_id.get()


def set_trace_id(tid: str = "") -> str:
    if not tid:
        tid = str(uuid4())[:8]
    _trace_id.set(tid)
    return tid


def get_trace_id() -> str:
    return _trace_id.get()
