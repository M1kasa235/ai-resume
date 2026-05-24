"""简历 RAG 服务 — 统一封装检索→重排序→生成 pipeline（简化版：纯向量+Reranker）"""

import asyncio
import logging
import time

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# 问题关键词 → 简历 section 映射（用于 section-aware 检索）
_SECTION_KEYWORDS: list[tuple[str, list[str]]] = [
    ("skills",       ["技能", "技术", "语言", "框架", "工具", "编程", "掌握", "熟练", "会用", "熟悉", "用过", "我会", "会"]),
    ("projects",     ["项目", "做过", "开发", "搭建", "参与", "上线", "负责过"]),
    ("work_experience", ["工作", "经历", "公司", "任职", "岗位", "入职", "离职", "跳槽"]),
    ("education",    ["教育", "学历", "学校", "毕业", "专业", "学位", "大学", "本科", "硕士"]),
    ("self_evaluation", ["自我评价", "优势", "特点", "性格", "个人总结", "关于我"]),
]


def _detect_sections(question: str) -> list[str]:
    """从用户问题中检测意图对应的简历 section"""
    matched = []
    for section, keywords in _SECTION_KEYWORDS:
        for kw in keywords:
            if kw in question:
                matched.append(section)
                break
    return matched or []  # 无匹配时返回空列表，走全库搜索


class ResumeRAGService:
    """简历 RAG 服务，对 agent 和 API 层屏蔽底层检索/生成细节"""

    def __init__(self, llm):
        from app.rag.core.vector_store import vector_store
        from app.rag.retrieval.reranker import DashScopeReranker
        from app.rag.pipeline.generator import RAGGenerator
        from app.rag.pipeline.resume_optimizer import ResumeDiagnoser, ResumeOptimizer, ResumePolisher
        from app.rag.pipeline.job_match import JobMatchService

        self.store = vector_store
        self.reranker = DashScopeReranker()
        self.generator = RAGGenerator(llm)
        self.diagnoser = ResumeDiagnoser(llm, vector_store, self.reranker)
        self.optimizer = ResumeOptimizer(llm, vector_store, self.reranker)
        self.polisher = ResumePolisher(llm)
        self.job_matcher = JobMatchService(vector_store, self.reranker, llm)

    async def _section_aware_search(
        self, query: str, user_id: int, k: int, question: str = "",
    ) -> list[Document]:
        """Section-aware 检索：检测意图 → 优先搜匹配 section → 不足时全库补齐"""
        sections = _detect_sections(question or query)

        if not sections:
            return await asyncio.to_thread(
                self.store.similarity_search, query, k, {"user_id": user_id}
            )

        # 逐 section 搜索并去重
        seen: set[str] = set()
        docs: list[Document] = []
        for section in sections:
            section_docs = await asyncio.to_thread(
                self.store.similarity_search, query, k, {"user_id": user_id, "section": section}
            )
            for d in section_docs:
                cid = d.metadata.get("chunk_id")
                if cid and cid not in seen:
                    seen.add(cid)
                    docs.append(d)

        # 不足时全库补齐
        if len(docs) < k:
            others = await asyncio.to_thread(
                self.store.similarity_search, query, k * 2, {"user_id": user_id}
            )
            for d in others:
                cid = d.metadata.get("chunk_id")
                if cid and cid not in seen:
                    seen.add(cid)
                    docs.append(d)
                if len(docs) >= k:
                    break

        return docs[:k]

    async def query(self, user_id: int, question: str) -> dict:
        """简历问答：section-aware 向量检索 + 重排序 + 生成"""
        t0 = time.time()
        docs = await self._section_aware_search(question, user_id, k=10, question=question)
        if not docs:
            return {"answer": "暂未找到相关的简历信息，请先上传简历。", "references": []}
        docs = await self.reranker.rerank(query=question, documents=docs, top_k=5)
        result = await self.generator.generate(query=question, context_docs=docs)
        logger.info(f"query: {int((time.time()-t0)*1000)}ms, k={len(docs)}")
        return result

    async def retrieve_raw_chunks(self, user_id: int, top_k: int = 15, focus: str = "") -> str:
        """纯检索：section-aware 向量搜索 + 重排序，不调用 LLM

        focus 可选值：technical（侧重技术/项目）、hr（侧重经历/软技能）、comprehensive（全覆盖）
        也可传自由文本描述需要侧重的内容维度。"""
        t0 = time.time()
        query = self._build_retrieval_query(focus)
        docs = await self._section_aware_search(query, user_id, k=top_k * 2)
        if not docs:
            return ""
        docs = await self.reranker.rerank(
            query=query,
            documents=docs,
            top_k=top_k,
        )
        parts = []
        for d in docs:
            content = d.page_content.strip()
            if content:
                parts.append(content)
        result = "\n\n---\n\n".join(parts)
        logger.info(f"retrieve_raw_chunks: {int((time.time()-t0)*1000)}ms, focus={focus!r}, chunks={len(docs)}")
        return result

    @staticmethod
    def _build_retrieval_query(focus: str) -> str:
        """根据面试类型/上下文构建自适应的检索 query"""
        mapping = {
            "technical": "技术栈 编程语言 框架 项目经验 系统设计 架构 算法 编码规范 性能优化",
            "hr": "工作经历 职业规划 团队协作 沟通表达 冲突处理 自我认知 薪资期望 管理经验",
            "comprehensive": "工作经历 技能 项目经验 教育背景 个人总结 职业规划 团队协作",
        }
        if focus and focus in mapping:
            return mapping[focus]
        if focus:
            return f"工作经历 技能 项目经验 教育背景 个人总结 {focus}"
        return "工作经历 技能 项目经验 教育背景 个人总结 实习经历 证书 获奖 语言能力 培训经历"

    async def diagnose(self, user_id: int) -> dict:
        return await self.diagnoser.diagnose(user_id)

    async def optimize_for_job(self, user_id: int, job_info: dict) -> dict:
        return await self.optimizer.optimize_for_job(user_id, job_info)

    async def polish(self, section: str, content: str) -> dict:
        return await self.polisher.polish(section, content)

    async def match_job(self, user_id: int, job) -> dict:
        return await self.job_matcher.match(user_id, job)