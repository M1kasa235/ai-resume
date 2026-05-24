"""岗位匹配服务 — 分析简历与岗位的匹配度（简化版：纯向量+Reranker）"""

import logging

from app.rag.core.utils import llm_response_text, parse_json_from_llm

logger = logging.getLogger(__name__)


class JobMatchService:
    """简历-岗位匹配分析，依赖注入 vector_store / reranker / llm"""

    def __init__(self, vector_store, reranker, llm):
        self.store = vector_store
        self.reranker = reranker
        self.llm = llm

    async def match(self, user_id: int, job) -> dict:
        """分析简历与岗位匹配度，返回评分和分析"""
        query = job.title + " " + (job.description[:200] if job.description else "")
        try:
            docs = self.store.similarity_search(query, k=10, filter={"user_id": user_id})
        except Exception:
            logger.error("岗位匹配检索失败 (user_id=%s)", user_id, exc_info=True)
            return {"overall_score": 0, "scores": [], "analysis": "检索服务暂时不可用，请稍后重试。", "suggestions": []}

        if not docs:
            return {"overall_score": 0, "scores": [], "analysis": "请先上传简历", "suggestions": []}

        try:
            docs = await self.reranker.rerank(query=job.title, documents=docs, top_k=5)
        except Exception:
            logger.error("岗位匹配重排序失败，回退到原始排序", exc_info=True)
            docs = docs[:5]

        resume_text = "\n".join(d.page_content for d in docs)

        prompt = (
            f"请分析该候选人与岗位的匹配度。\n\n"
            f"=== 候选人简历 ===\n{resume_text}\n\n"
            f"=== 岗位信息 ===\n"
            f"公司：{job.company_name}\n"
            f"岗位：{job.title}\n"
            f"薪资：{job.salary_min}-{job.salary_max}k\n"
            f"城市：{job.city or '不限'}\n"
            f"描述：{job.description or ''}\n"
            f"要求：{job.requirements or ''}\n"
            f"技能要求：{', '.join(job.skills_required) if job.skills_required else ''}\n\n"
            f"请按以下维度打分（0-10分），附理由：\n"
            f"1. 技能匹配度\n"
            f"2. 经验匹配度\n"
            f"3. 城市匹配度\n"
            f"4. 综合评分（综合以上三个维度的整体评分）\n\n"
            f"输出JSON格式：\n"
            f'{{"scores":[{{"dimension":"技能匹配度","score":8,"reason":"..."}}],'
            f'"analysis":"总结分析","suggestions":["建议1","建议2"]}}'
        )

        try:
            resp = await self.llm.ainvoke(prompt)
            text = llm_response_text(resp)
        except Exception:
            logger.error("岗位匹配 LLM 调用失败", exc_info=True)
            return {"overall_score": 0, "scores": [], "analysis": "匹配分析服务暂时不可用，请稍后重试。", "suggestions": []}

        data = parse_json_from_llm(text)
        if not data:
            return {"overall_score": 0, "scores": [], "analysis": text, "suggestions": []}

        score_list = data.get("scores", [])

        overall = 0
        sub_scores = []
        for s in score_list:
            if "综合" in s.get("dimension", ""):
                overall = s["score"]
            else:
                sub_scores.append(s)
        if overall == 0 and sub_scores:
            overall = sum(s["score"] for s in sub_scores) / len(sub_scores)
        elif overall == 0 and score_list:
            overall = sum(s["score"] for s in score_list) / len(score_list)

        overall = overall / 10 if overall > 1 else overall
        normalized_scores = []
        for s in score_list:
            score_val = s["score"]
            normalized_scores.append({
                "dimension": s["dimension"],
                "score": (score_val / 10) if score_val > 1 else score_val,
                "reason": s.get("reason", ""),
            })

        overall = max(0.0, min(1.0, overall))

        return {
            "overall_score": round(overall, 4),
            "scores": normalized_scores,
            "analysis": data.get("analysis", ""),
            "suggestions": data.get("suggestions", []),
        }