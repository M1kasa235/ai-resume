"""RAG 基础设施 — 向量检索、重排序、生成、服务层"""

from functools import lru_cache


@lru_cache()
def get_rag_service():
    """获取 ResumeRAGService 单例（延迟加载，避免 import 时拉入 LLM）"""
    from app.rag.services.resume_service import ResumeRAGService
    from app.core.llm import get_structured_model
    return ResumeRAGService(get_structured_model())


@lru_cache()
def get_knowledge_service():
    """获取 KnowledgeService 单例"""
    from app.rag.services.knowledge_service import KnowledgeService
    return KnowledgeService()
