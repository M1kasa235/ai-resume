"""AgentRegistry — 统一 Agent 生命周期管理，消除散落的 get_xxx_agent 单例模式"""

from typing import Any, Callable

logger = __import__("logging").getLogger(__name__)


class AgentRegistry:
    """所有 agent 的懒加载缓存中心"""

    _agents: dict[str, Any] = {}

    @classmethod
    def get_or_create(cls, name: str, factory: Callable[[], Any]) -> Any:
        if name not in cls._agents:
            cls._agents[name] = factory()
        return cls._agents[name]

    @classmethod
    def clear(cls, name: str = ""):
        """清除缓存（测试用）"""
        if name:
            cls._agents.pop(name, None)
        else:
            cls._agents.clear()
