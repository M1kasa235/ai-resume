"""知识库检索服务 — 向量+BM25+RRF 混合检索 + Parent/Child 两阶段

Stage 0: 向量 + BM25 → RRF 融合
Stage 1: DashScope Reranker 重排序
Stage 2: 父文档拉取（完整上下文）
"""

import logging
import time
from typing import Optional

from app.rag.core.vector_store import knowledge_vector_store
from app.rag.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库语义检索，完整流水线"""

    def __init__(self):
        self.hybrid = HybridRetriever(
            vector_store=knowledge_vector_store,
            filter_fn=lambda dt: {"chunk_type": "child", **({"doc_type": dt} if dt else {})},
        )

    def invalidate_partition(self, doc_type: str):
        """数据变更后调用，清除 BM25 缓存，下次检索重建索引"""
        self.hybrid.invalidate_partition(doc_type)

    async def search(self, query: str, limit: int = 5, doc_type: Optional[str] = None) -> list[dict]:
        """完整检索流水线

        Args:
            query: 用户查询
            limit: 返回结果数量
            doc_type: 知识分区过滤 (None=全部, "job", "resume_guide", "interview")
        """
        t0 = time.time()
        k_stage0 = limit  # retrieve() 内部 multiplier=2 控制各源取 k*2

        # ══════ Stage 0: 混合检索（向量 + BM25 → 加权 RRF 融合）══════
        candidates = await self.hybrid.retrieve(query, doc_type, k=k_stage0)
        t1 = time.time()

        if not candidates:
            return []

        # ══════ Stage 1: 重排序 ══════
        try:
            from app.rag.retrieval.reranker import DashScopeReranker
            reranker = DashScopeReranker()
            ranked = await reranker.rerank(query, candidates, top_k=limit)
        except Exception:
            logger.warning("Reranker 异常，退化为 RRF top-k", exc_info=True)
            ranked = candidates[:limit]

        if not ranked:
            ranked = candidates[:limit]
        t2 = time.time()

        # ══════ Stage 2: Parent 膨胀 ══════
        parent_ids = []
        seen = set()
        for d in ranked:
            pid = d.metadata.get("parent_id")
            if pid and pid not in seen:
                seen.add(pid)
                parent_ids.append(pid)

        if not parent_ids:
            return self._docs_to_results(ranked)

        # 批量拉取 parent chunks
        parent_docs = self._fetch_parents_batch(parent_ids)

        if not parent_docs:
            results = self._docs_to_results(ranked)
        else:
            parent_map: dict[str, dict] = {}
            for d in parent_docs:
                pid = d.get("parent_id", "")
                if pid and pid not in parent_map:
                    parent_map[pid] = d
            ordered_parent_docs = [parent_map[pid] for pid in parent_ids if pid in parent_map]
            results = [
                {
                    "title": d.get("metadata", {}).get("title", ""),
                    "category": d.get("metadata", {}).get("category", ""),
                    "content": d.get("content", "").strip(),
                    "parent_id": d.get("parent_id", ""),
                }
                for d in ordered_parent_docs
            ] or self._docs_to_results(ranked)
        logger.info(
            f"knowledge_search: total={int((time.time()-t0)*1000)}ms "
            f"hybrid={int((t1-t0)*1000)}ms rerank={int((t2-t1)*1000)}ms "
            f"k={len(results)}"
        )
        return results

    def _fetch_parents_batch(self, parent_ids: list[str]) -> list[dict]:
        """批量一次拉取所有 parent chunks"""
        try:
            results = knowledge_vector_store.db.get(
                where={"$and": [{"chunk_type": "parent"}, {"parent_id": {"$in": parent_ids}}]},
                limit=len(parent_ids) * 2,
            )
        except Exception:
            logger.warning("批量拉取 parent 失败，退化为逐个查询", exc_info=True)
            return self._fetch_parents_one_by_one(parent_ids)

        docs = []
        for i in range(len(results.get("ids", []))):
            meta = results["metadatas"][i] if i < len(results.get("metadatas", [])) else {}
            if meta.get("chunk_type") != "parent":
                continue
            docs.append({
                "content": results["documents"][i],
                "parent_id": meta.get("parent_id", ""),
                "metadata": meta,
            })
        return docs

    def _fetch_parents_one_by_one(self, parent_ids: list[str]) -> list[dict]:
        """逐个查询 parent（批量失败时的退化路径）"""
        docs = []
        seen = set()
        for pid in parent_ids:
            if pid in seen:
                continue
            seen.add(pid)
            try:
                results = knowledge_vector_store.db.get(where={"parent_id": pid})
                for i in range(len(results.get("ids", []))):
                    meta = results["metadatas"][i] if i < len(results.get("metadatas", [])) else {}
                    if meta.get("chunk_type") != "parent":
                        continue
                    docs.append({
                        "content": results["documents"][i],
                        "parent_id": pid,
                        "metadata": meta,
                    })
            except Exception:
                logger.warning("拉取 parent chunk 失败 (parent_id=%s)", pid, exc_info=True)
                continue
        return docs

    @staticmethod
    def _docs_to_results(docs) -> list[dict]:
        results = []
        for d in docs:
            results.append({
                "title": d.metadata.get("title", ""),
                "category": d.metadata.get("category", ""),
                "content": d.page_content[:500],
                "parent_id": d.metadata.get("parent_id", ""),
            })
        return results
