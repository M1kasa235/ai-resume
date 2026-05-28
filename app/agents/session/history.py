"""Session history read/clear via LangGraph checkpointer with Redis cache."""

import json
import logging

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.config import create_checkpointer
from app.agents.session.message_display import normalize_user_message_for_display
from app.agents.session.presentation import normalize_assistant_content
from app.core.config import settings

logger = logging.getLogger(__name__)

CACHE_PREFIX = "session:history:"


def _serialize_messages(messages: list[dict[str, str]]) -> str:
    return json.dumps(messages, ensure_ascii=False)


def _deserialize_messages(data: str) -> list[dict[str, str]]:
    return json.loads(data)


async def _cache_get(key: str) -> list[dict[str, str]] | None:
    from app.core.redis import get_redis

    r = get_redis()
    if r is None:
        return None
    try:
        data = await r.get(key)
        return _deserialize_messages(data) if data else None
    except Exception:
        return None


async def _cache_set(key: str, messages: list[dict[str, str]]) -> None:
    from app.core.redis import get_redis

    r = get_redis()
    if r is None:
        return
    try:
        await r.setex(key, settings.REDIS_SESSION_CACHE_TTL, _serialize_messages(messages))
    except Exception:
        pass


async def _cache_delete(key: str) -> None:
    from app.core.redis import get_redis

    r = get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        pass


async def get_chat_history(thread_id: str) -> list[dict[str, str]]:
    cache_key = f"{CACHE_PREFIX}{thread_id}"

    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached

    logger.info("获取历史消息，thread_id: %s", thread_id)
    checkpoint = await create_checkpointer().aget({"configurable": {"thread_id": thread_id}})
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
            content = msg.content
            if isinstance(content, str):
                content = normalize_user_message_for_display(content)
            result.append({"role": "user", "content": content})
        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, str):
                content = normalize_assistant_content(content)
            result.append({"role": "assistant", "content": content})

    await _cache_set(cache_key, result)
    return result


async def clear_chat_history(thread_id: str) -> None:
    logger.info("清空历史消息，thread_id: %s", thread_id)
    await create_checkpointer().adelete_thread(thread_id)
    await _cache_delete(f"{CACHE_PREFIX}{thread_id}")

