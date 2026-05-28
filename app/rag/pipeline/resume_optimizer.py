"""简历优化引擎：诊断、定向优化、润色（简化版：纯向量+Reranker 替代 RAGRetriever）"""

import asyncio
import logging

from langchain_core.language_models import BaseChatModel

from app.agents.context.temporal import TEMPORAL_REASONING_RULES, reference_date
from app.rag.core.utils import parse_json_from_llm, llm_response_text

logger = logging.getLogger(__name__)


class ResumeDiagnoser:
    """简历诊断"""

    def __init__(self, llm: BaseChatModel, vector_store, reranker):
        self.llm = llm
        self.store = vector_store
        self.reranker = reranker

    async def diagnose(self, user_id: int) -> dict:
        """分析简历整体优劣势"""
        query = "简历整体诊断分析 技能 经验 项目 教育 优势 不足"
        docs = await asyncio.to_thread(
            self.store.similarity_search, query, 15, {"user_id": user_id}
        )
        if not docs:
            return {"error": "请先上传简历"}

        docs = await self.reranker.rerank(query=query, documents=docs, top_k=10)

        resume_text = "\n".join(d.page_content for d in docs)

        today = reference_date()
        prompt = (
            f"{TEMPORAL_REASONING_RULES}\n\n"
            f"参考日期（今天）：{today}\n"
            "你是一位资深HR。分析以下简历，输出诊断报告。\n\n"
            "简历内容：\n{resume_text}\n\n"
            "按 JSON 格式输出：\n"
            '{{\n'
            '  "overall_score": "7/10",\n'
            '  "strengths": ["优势1", "优势2"],\n'
            '  "weaknesses": ["不足1", "不足2"],\n'
            '  "suggestions": [\n'
            '    {{"section": "项目经验", "issue": "描述简单", "advice": "建议增加量化数据"}}\n'
            '  ]\n'
            '}}'
        ).format(resume_text=resume_text)

        try:
            resp = await self.llm.ainvoke(prompt)
            text = llm_response_text(resp)
        except Exception:
            logger.error("简历诊断 LLM 调用失败", exc_info=True)
            return {"error": "诊断服务暂时不可用，请稍后重试。"}

        result = parse_json_from_llm(text)
        if result:
            return result
        return {"overall_score": "N/A", "raw_response": text}


class ResumeOptimizer:
    """简历定向优化"""

    def __init__(self, llm: BaseChatModel, vector_store, reranker):
        self.llm = llm
        self.store = vector_store
        self.reranker = reranker

    async def optimize_for_job(self, user_id: int, job_info: dict) -> dict:
        """针对目标岗位优化简历"""
        query = f"{job_info.get('title', '')} {job_info.get('description', '')[:200]}"
        docs = await asyncio.to_thread(
            self.store.similarity_search, query, 15, {"user_id": user_id}
        )
        if not docs:
            return {"error": "请先上传简历"}

        docs = await self.reranker.rerank(query=query, documents=docs, top_k=10)

        resume_text = "\n".join(d.page_content for d in docs)

        prompt = (
            "你是一位资深简历优化专家。针对目标岗位优化简历。\n\n"
            "原始简历：\n{resume_text}\n\n"
            "目标岗位信息：\n"
            "- 公司：{company}\n"
            "- 岗位：{title}\n"
            "- 要求：{requirements}\n"
            "- 职责：{description}\n\n"
            "优化要求：\n"
            "1. 突出与岗位匹配的技能和经验\n"
            "2. 项目描述用 STAR 法则（情境→任务→行动→结果）\n"
            "3. 增加量化数据\n"
            "4. 保持真实性，不编造经历\n\n"
            "输出 JSON 格式：\n"
            '{{\n'
            '  "optimized_sections": [\n'
            '    {{"section": "项目经验", "original": "...", "optimized": "...", "change_reason": "..."}}\n'
            '  ],\n'
            '  "full_resume": "优化后的完整简历文本",\n'
            '  "summary": {{"changes": ["改动1"], "match_score_before": 6, "match_score_after": 8}}\n'
            '}}'
        ).format(
            resume_text=resume_text,
            company=job_info.get("company_name", ""),
            title=job_info.get("title", ""),
            requirements=job_info.get("requirements", ""),
            description=job_info.get("description", ""),
        )

        try:
            resp = await self.llm.ainvoke(prompt)
            text = llm_response_text(resp)
        except Exception:
            logger.error("简历优化 LLM 调用失败", exc_info=True)
            return {"error": "优化服务暂时不可用，请稍后重试。"}

        result = parse_json_from_llm(text)
        if result:
            return result
        return {"raw_response": text}


class ResumePolisher:
    """单段润色"""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def polish(self, section: str, content: str) -> dict:
        prompt = (
            f"你是简历优化专家。请优化以下{section}的描述。\n\n"
            f"原始内容：\n{content}\n\n"
            f"要求：\n"
            f"1. 使用 STAR 法则\n"
            f"2. 增加量化数据\n"
            f"3. 动词开头，突出价值\n"
            f"4. 保持真实性\n\n"
            f"输出 JSON：\n"
            f'{{"original": "...", "optimized": "...", "change_reason": "..."}}'
        )

        try:
            resp = await self.llm.ainvoke(prompt)
            text = llm_response_text(resp)
        except Exception:
            logger.error("简历润色 LLM 调用失败", exc_info=True)
            return {"error": "润色服务暂时不可用，请稍后重试。"}

        result = parse_json_from_llm(text)
        if result:
            return result
        return {"original": content, "optimized": text, "change_reason": ""}