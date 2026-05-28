"""User-facing error messages for agent streaming."""

from app.core.config import settings


def agent_stream_error_message(exc: Exception) -> str:
    """Return a safe message for SSE clients; include detail only in DEBUG."""
    message = str(exc)
    if "recursion limit" in message.lower() or "GRAPH_RECURSION_LIMIT" in message:
        user_msg = "处理超时：任务步骤过多，请简化问题或拆成两次提问（如先查简历、再要岗位推荐）。"
        return f"{user_msg} ({exc})" if settings.DEBUG else user_msg
    if settings.DEBUG:
        return f"处理失败：{exc}"
    return "处理失败，请稍后重试。"
