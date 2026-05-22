"""模型实例 — 从 core/llm 导入工厂函数，保持向后兼容"""
from app.core.llm import get_chat_model, get_structured_model

__all__ = ["get_chat_model", "get_structured_model"]