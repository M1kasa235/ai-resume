"""LLM 模型实例集中管理 — 按场景分配不同 temperature（懒加载，避免 import 时初始化）"""

from langchain.chat_models import init_chat_model
from app.core.config import settings

_MODEL_NAME = "deepseek-v4-flash"

_chat_model = None
_structured_model = None


def _resolve_base_url() -> str | None:
    """优先使用显式配置的 base_url，避免把 API Key 当 URL。"""
    return settings.DEEPSEEK_BASE_URL or settings.DASHSCOPE_BASE_URL or None


def _thinking_extra_body() -> dict:
    """DeepSeek thinking 与 LangChain 工具调用不兼容，默认关闭。"""
    mode = "enabled" if settings.DEEPSEEK_THINKING_ENABLED else "disabled"
    return {"thinking": {"type": mode}}


def _init_deepseek_model(*, temperature: float):
    return init_chat_model(
        model=_MODEL_NAME,
        model_provider="openai",
        temperature=temperature,
        base_url=_resolve_base_url(),
        api_key=settings.DEEPSEEK_API_KEY,
        extra_body=_thinking_extra_body(),
    )


def get_chat_model():
    """懒加载对话模型（temperature 0.7），适合聊天对话"""
    global _chat_model
    if _chat_model is None:
        _chat_model = _init_deepseek_model(temperature=0.7)
    return _chat_model


def get_structured_model():
    """懒加载结构化模型（temperature 0.3），适合 RAG 问答、简历诊断/优化"""
    global _structured_model
    if _structured_model is None:
        _structured_model = _init_deepseek_model(temperature=0.3)
    return _structured_model
