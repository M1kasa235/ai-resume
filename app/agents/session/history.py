"""Session history read/clear via LangGraph checkpointer."""

import logging

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.config import create_checkpointer

logger = logging.getLogger(__name__)


def get_chat_history(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    logger.info("获取历史消息，thread_id: %s", thread_id)
    checkpoint = create_checkpointer().get({"configurable": {"thread_id": thread_id}})
    if not checkpoint:
        return []
    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []
    messages = channel_values.get("messages", [])
    if not messages:
        return []
    result = []
    for msg in messages:
        if not msg.content:
            continue
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
    return result


def clear_chat_history(thread_id: str):
    """清空会话"""
    logger.info("清空历史消息，thread_id: %s", thread_id)
    create_checkpointer().delete_thread(thread_id)
