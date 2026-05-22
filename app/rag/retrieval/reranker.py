"""Reranker 重排 — 使用阿里百炼 DashScope gte-rerank-v2 模型"""

import asyncio
import logging

from langchain_core.documents import Document
from app.core.config import settings

logger = logging.getLogger(__name__)


class DashScopeReranker:
    """使用阿里百炼 DashScope gte-rerank-v2 模型重排

    gte-rerank-v2 单文档上限 4000 tokens，中文约 4000 字符。
    """

    def __init__(self, model: str = "gte-rerank-v2", max_chars: int = 4000):
        self.model = model
        self.api_key = settings.DASHSCOPE_API_KEY
        self.max_chars = max_chars

    async def rerank(self, query: str, documents: list[Document], top_k: int = 5) -> list[Document]:
        if not documents:
            return []

        if len(documents) <= top_k:
            return documents[:top_k]

        import dashscope
        dashscope.api_key = self.api_key

        try:
            resp = await asyncio.to_thread(
                dashscope.TextReRank.call,
                model=self.model,
                query=query,
                documents=[doc.page_content[:self.max_chars] for doc in documents],
                top_n=top_k,
            )
        except Exception:
            logger.warning(
                "DashScope rerank 异常, 回退到原始排序, "
                "model=%s, query_len=%d, doc_count=%d",
                self.model, len(query), len(documents),
                exc_info=True,
            )
            return documents[:top_k]

        if resp.status_code != 200:
            logger.warning(
                "DashScope rerank 失败 (status=%s), 回退到原始排序, "
                "model=%s, query_len=%d, doc_count=%d",
                resp.status_code, self.model, len(query), len(documents)
            )
            return documents[:top_k]

        ranked = resp.output["results"]
        scores = [f"{r['relevance_score']:.2f}" for r in ranked]
        logger.info(f"rerank scores: [{', '.join(scores)}] query={query[:60]!r}")
        return [documents[item["index"]] for item in ranked if 0 <= item["index"] < len(documents)][:top_k]