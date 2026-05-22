"""混合检索：向量 + BM25 关键词，RRF 融合（参数化版本，可用于简历库和知识库）"""

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Callable, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_jieba_ready = False

TECH_TERMS = [
    # 编程语言
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Golang", "Rust", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Dart",
    # 前端
    "React", "Vue", "Vue3", "Angular", "Next.js", "Nuxt", "Svelte", "Webpack", "Vite",
    "HTML5", "CSS3", "Sass", "Tailwind", "Bootstrap", "jQuery", "Redux", "Pinia",
    # 后端框架
    "Django", "Flask", "FastAPI", "Spring", "SpringBoot", "MyBatis", "Hibernate",
    "Express", "NestJS", "Gin", "Echo", "Rails", "Laravel",
    # 数据库
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "ClickHouse", "TiDB",
    "SQLite", "Oracle", "SQLServer", "Cassandra", "Neo4j", "HBase", "Hive",
    # 云原生 / DevOps
    "Docker", "Kubernetes", "K8s", "Jenkins", "GitLab", "GitHub", "CI/CD",
    "Terraform", "Ansible", "Prometheus", "Grafana", "ELK", "Nginx", "Envoy",
    "Istio", "Helm", "ArgoCD",
    # 云平台
    "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云",
    # 大数据
    "Hadoop", "Spark", "Flink", "Kafka", "RabbitMQ", "Pulsar", "ZooKeeper",
    "Airflow", "DolphinScheduler", "DataX",
    # AI / ML
    "LLM", "RAG", "NLP", "CV", "Transformer", "BERT", "GPT", "PyTorch", "TensorFlow",
    "Keras", "Scikit-learn", "Pandas", "NumPy", "LangChain", "LlamaIndex",
    "embedding", "fine-tuning", "AIGC",
    # 移动端
    "Android", "iOS", "Flutter", "ReactNative", "UniApp", "小程序",
    # 测试
    "Selenium", "JUnit", "pytest", "JMeter", "Cypress", "Playwright",
    # 通用技术术语
    "API", "SDK", "CLI", "SaaS", "PaaS", "IaaS", "RESTful", "GraphQL", "gRPC",
    "WebSocket", "OAuth", "JWT", "SSO", "RBAC", "DevOps", "DevSecOps", "SRE",
    "微服务", "高并发", "分布式", "高可用",
]


def _init_jieba():
    global _jieba_ready
    if _jieba_ready:
        return
    import jieba
    for term in TECH_TERMS:
        jieba.add_word(term)
    _jieba_ready = True


class HybridRetriever:
    """向量 + BM25 混合检索，Reciprocal Rank Fusion 融合结果

    参数化设计：通过构造注入 vector_store 和 filter_fn，适配不同数据源。
    - 简历库：HybridRetriever(vector_store, lambda uid: {"user_id": uid})
    - 知识库：HybridRetriever(knowledge_vector_store, lambda dt: {"chunk_type": "child", "doc_type": dt})
    """

    _MAX_PARTITIONS = 200  # BM25 索引最大分区数，超出按 LRU 淘汰

    # RRF 权重常量
    _BM25_KEYWORD_WEIGHT = 1.5   # 关键词查询时 BM25 的额外权重
    _KEYWORD_DENSITY_THRESHOLD = 0.08  # 技术术语密度阈值（术语数/总字数）

    def __init__(self, vector_store, filter_fn: Optional[Callable] = None):
        self.vector_store = vector_store
        self.filter_fn = filter_fn or (lambda key: {})
        self._bm25_indexes: OrderedDict = OrderedDict()  # key → BM25Okapi (LRU)
        self._bm25_docs: OrderedDict = OrderedDict()     # key → list[Document] (LRU)
        self._bm25_empty: set = set()                    # key → known empty

    # ── 查询特征检测 ──

    @classmethod
    def _detect_query_weights(cls, query: str) -> tuple[float, float]:
        """根据查询特征返回 (weight_vector, weight_bm25)

        技术术语密度高 → 偏重 BM25（关键词匹配更准）
        自然语言问题 → 等权重（语义向量更擅长理解意图）
        """
        query_lower = query.lower()
        hits = sum(1 for term in TECH_TERMS if term.lower() in query_lower)
        density = hits / max(len(query), 1)
        if density >= cls._KEYWORD_DENSITY_THRESHOLD:
            return 1.0, cls._BM25_KEYWORD_WEIGHT
        return 1.0, 1.0

    # ── 知识库用 ──

    async def retrieve(
        self, query: str, partition_key, k: int = 10, multiplier: float = 2.0,
    ) -> list[Document]:
        """混合检索：向量 + BM25 并行 → 加权 RRF 融合

        Args:
            query: 查询文本
            partition_key: 分区键（简历 user_id / 知识库 doc_type）
            k: 返回数量
            multiplier: 各检索源取 k * multiplier 条供 RRF 融合（默认 2.0）
        """
        f = self.filter_fn(partition_key) if callable(self.filter_fn) else {}
        fetch_k = max(k, int(k * multiplier))

        # 向量检索和 BM25 检索并行执行（I/O + CPU 不互斥）
        t0 = time.time()
        vector_task = asyncio.to_thread(
            self.vector_store.similarity_search, query, k=fetch_k, filter=f,
        )
        bm25_task = asyncio.to_thread(
            self._bm25_search, query, partition_key, k=fetch_k, where=f,
        )
        vector_docs, bm25_docs = await asyncio.gather(vector_task, bm25_task)
        t1 = time.time()

        # 加权 RRF 融合
        w_vec, w_bm25 = self._detect_query_weights(query)
        result = self._rrf(vector_docs, bm25_docs, k=k, weight_vector=w_vec, weight_bm25=w_bm25)
        logger.info(
            f"hybrid_retrieve: total={int((time.time()-t0)*1000)}ms "
            f"parallel={int((t1-t0)*1000)}ms "
            f"vector={len(vector_docs)} bm25={len(bm25_docs)} → rrf={len(result)} "
            f"weights=(v={w_vec:.1f}, b={w_bm25:.1f})"
        )
        return result

    def invalidate_partition(self, partition_key):
        """分区数据变更后调用，下次检索重建 BM25 索引"""
        self._bm25_indexes.pop(partition_key, None)
        self._bm25_docs.pop(partition_key, None)
        self._bm25_empty.discard(partition_key)

    # ── 简历兼容（向后兼容旧接口） ──

    def invalidate_user(self, user_id: int):
        """兼容旧简历接口"""
        self.invalidate_partition(user_id)

    # ── BM25 (with LRU) ──

    def _bm25_search(self, query: str, partition_key, k: int, where: Optional[dict] = None) -> list[Document]:
        import jieba
        from rank_bm25 import BM25Okapi

        _init_jieba()

        if partition_key in self._bm25_empty:
            return []

        if partition_key not in self._bm25_indexes:
            # Chroma get() 要求单 key filter，多 key 需转为 $and
            chroma_where = _to_chroma_where(where) if where else None
            results = self.vector_store.db.get(where=chroma_where, limit=10000)
            ids = results.get("ids", [])
            if not ids:
                self._bm25_empty.add(partition_key)
                return []
            docs = [
                Document(
                    page_content=results["documents"][i],
                    metadata=results["metadatas"][i],
                )
                for i in range(len(ids))
            ]
            tokenized = [list(jieba.cut(d.page_content)) for d in docs]
            self._bm25_indexes[partition_key] = BM25Okapi(tokenized)
            self._bm25_docs[partition_key] = docs
            self._maybe_evict()

        self._bm25_indexes.move_to_end(partition_key)
        self._bm25_docs.move_to_end(partition_key)

        bm25 = self._bm25_indexes[partition_key]
        tokenized_query = list(jieba.cut(query))
        scores = bm25.get_scores(tokenized_query)
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        docs = self._bm25_docs[partition_key]
        return [docs[i] for i in top if scores[i] > 0]

    def _maybe_evict(self):
        while len(self._bm25_indexes) > self._MAX_PARTITIONS:
            self._bm25_indexes.popitem(last=False)
        while len(self._bm25_docs) > self._MAX_PARTITIONS:
            self._bm25_docs.popitem(last=False)

    # ── 加权 RRF 融合 ──

    @staticmethod
    def _rrf(
        vector_docs: list[Document],
        bm25_docs: list[Document],
        k: int,
        constant: int = 60,
        weight_vector: float = 1.0,
        weight_bm25: float = 1.0,
    ) -> list[Document]:
        """Reciprocal Rank Fusion，支持向量/BM25 非等权融合

        RRF 公式: score(d) = Σ w_i / (constant + rank_i(d) + 1)
        默认 weight_vector = weight_bm25 = 1.0（标准 RRF）
        关键词查询时 weight_bm25 > 1.0 可以让 BM25 的排序更占优势
        """
        scores: dict[str, float] = {}
        for rank, doc in enumerate(vector_docs):
            cid = doc.metadata.get("chunk_id")
            if cid:
                scores[cid] = scores.get(cid, 0) + weight_vector / (constant + rank + 1)
        for rank, doc in enumerate(bm25_docs):
            cid = doc.metadata.get("chunk_id")
            if cid:
                scores[cid] = scores.get(cid, 0) + weight_bm25 / (constant + rank + 1)

        sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)[:k]

        doc_map = {}
        for doc in vector_docs:
            cid = doc.metadata.get("chunk_id")
            if cid:
                doc_map[cid] = doc
        for doc in bm25_docs:
            cid = doc.metadata.get("chunk_id")
            if cid:
                doc_map[cid] = doc

        return [doc_map[cid] for cid in sorted_ids if cid in doc_map]


def _to_chroma_where(where: dict) -> dict:
    """Chroma get() 只接受单操作符 filter，多 key 转为 $and"""
    if len(where) <= 1:
        return where
    return {"$and": [{k: v} for k, v in where.items()]}