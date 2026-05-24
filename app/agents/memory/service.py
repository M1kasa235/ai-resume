"""MemoryService facade — composes all memory capabilities."""

from app.agents.memory.base import MemoryStoreBase
from app.agents.memory.repository import MemoryRepositoryMixin
from app.agents.memory.retrieval import MemoryRetrievalMixin
from app.agents.memory.events import MemoryEventsMixin
from app.agents.memory.extraction import MemoryExtractionMixin
from app.agents.memory.maintenance import MemoryMaintenanceMixin


class MemoryService(
    MemoryRepositoryMixin,
    MemoryRetrievalMixin,
    MemoryEventsMixin,
    MemoryExtractionMixin,
    MemoryMaintenanceMixin,
    MemoryStoreBase,
):
    """事件驱动长期记忆服务（单例）。"""

