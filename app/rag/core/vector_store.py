"""Chroma 向量库管理 — 使用阿里百炼 embedding"""

import os
from typing import Optional, List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from pydantic import BaseModel

from app.core.config import settings

# 向量库持久化路径
CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "db",
    "chroma"
)

COLLECTION_RESUME = "resume_chunks"
COLLECTION_KNOWLEDGE = "knowledge_base"

_embedding_instance = None


class DashScopeEmbeddings(BaseModel):
    """使用阿里百炼 DashScope API 的 embedding 封装"""

    model: str = settings.RAG_EMBEDDING_MODEL
    api_key: str = ""

    class Config:
        arbitrary_types_allowed = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量 embedding（空字符串守卫：替换为单空格避免 DashScope 报错）"""
        import dashscope

        dashscope.api_key = self.api_key
        results = []
        # DashScope text-embedding-v4 单次最大 10 条
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # 守卫：空字符串导致 DashScope 400 (Range of input length [1, 8192])
            batch = [t if t and t.strip() else " " for t in batch]
            resp = dashscope.TextEmbedding.call(
                model=self.model,
                input=batch,
            )
            if resp.status_code == 200:
                for item in resp.output["embeddings"]:
                    results.append(item["embedding"])
            else:
                raise RuntimeError(f"DashScope embedding error: {resp}")
        return results

    def embed_query(self, text: str) -> List[float]:
        """单个文本 embedding"""
        return self.embed_documents([text])[0]


def get_embedding_model():
    """获取阿里百炼 embedding（懒加载 + 缓存）"""
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    _embedding_instance = DashScopeEmbeddings(
        model=settings.RAG_EMBEDDING_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
    )
    return _embedding_instance


class VectorStore:
    """向量库操作封装"""

    def __init__(self, collection_name: str = COLLECTION_RESUME):
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        self.collection_name = collection_name
        self._db = None  # 懒加载

    @property
    def db(self):
        if self._db is None:
            self._db = Chroma(
                collection_name=self.collection_name,
                embedding_function=get_embedding_model(),
                persist_directory=CHROMA_PERSIST_DIR,
            )
        return self._db

    def add_documents(self, documents: list[Document]) -> list[str]:
        """写入文档，返回文档 ID 列表"""
        return self.db.add_documents(documents)

    @staticmethod
    def _normalize_filter(filter: Optional[dict]) -> Optional[dict]:
        """兼容 Chroma 多条件过滤：普通多 key dict 自动转 $and。"""
        if not filter:
            return filter
        if "$and" in filter or "$or" in filter:
            return filter
        if len(filter) <= 1:
            return filter
        return {"$and": [{k: v} for k, v in filter.items()]}

    def _collect_ids(self, filter: Optional[dict] = None, batch_size: int = 1000) -> list[str]:
        """按过滤条件收集全部 ID（支持分页，避免一次性大结果）。"""
        where = self._normalize_filter(filter)
        ids: list[str] = []
        offset = 0
        while True:
            try:
                results = self.db.get(where=where, limit=batch_size, offset=offset)
            except TypeError:
                # 某些 Chroma 版本不支持 offset，回退到一次性查询
                results = self.db.get(where=where)
                return results.get("ids", [])
            batch_ids = results.get("ids", [])
            if not batch_ids:
                break
            ids.extend(batch_ids)
            if len(batch_ids) < batch_size:
                break
            offset += len(batch_ids)
        return ids

    def similarity_search(
        self, query: str, k: int = 10, filter: Optional[dict] = None
    ) -> list[Document]:
        """相似度检索"""
        where = self._normalize_filter(filter)
        return self.db.similarity_search(query, k=k, filter=where)

    def delete_ids(self, ids: list[str], batch_size: int = 500):
        """按 ID 批量删除（分批，避免单次 payload 过大）。"""
        if not ids:
            return
        for i in range(0, len(ids), batch_size):
            self.db.delete(ids=ids[i : i + batch_size])

    def delete_by_filter(self, filter: dict):
        """按条件删除文档"""
        ids = self._collect_ids(filter)
        self.delete_ids(ids)

    def get_user_chunks(self, user_id: int) -> list[Document]:
        """获取指定用户的所有简历块（不依赖语义检索）"""
        results = self.db.get(where=self._normalize_filter({"user_id": user_id}))
        docs = []
        for i in range(len(results.get("ids", []))):
            docs.append(Document(
                page_content=results["documents"][i],
                metadata=results["metadatas"][i],
            ))
        return docs

    def list_ids_by_filter(self, filter: Optional[dict] = None) -> list[str]:
        """返回满足过滤条件的全部文档 ID。"""
        return self._collect_ids(filter)

    def delete_user_chunks(self, user_id: int):
        """删除指定用户的所有简历块"""
        self.delete_by_filter({"user_id": user_id})

    def count(self, filter: Optional[dict] = None) -> int:
        """统计文档数量"""
        return len(self._collect_ids(filter))


# 单例（懒加载，不会在 import 时调 API）
vector_store = VectorStore()

# 通用知识库 collection（岗位、简历指导、面试等共享知识）
knowledge_vector_store = VectorStore(COLLECTION_KNOWLEDGE)