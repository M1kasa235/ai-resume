"""RAG 问答生成"""

import logging

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from app.rag.core.utils import llm_response_text

logger = logging.getLogger(__name__)


_NO_INFO_MARKERS = ("简历中未提及", "未提及", "简历中没有")


QA_PROMPT_TEMPLATE = (
    "你是一个专业的简历分析师。根据提供的简历片段回答用户的问题。\n\n"
    "=== 简历片段 ===\n{context}\n\n"
    "=== 用户问题 ===\n{question}\n\n"
    "=== 回答要求 ===\n"
    "1. 只基于上面提供的简历片段回答\n"
    "2. 如果简历片段中没有相关信息，明确说'简历中未提及'\n"
    "3. 引用具体的简历内容作为依据\n"
    "4. 用中文回答"
)


class RAGGenerator:
    """RAG 问答生成"""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate(self, query: str, context_docs: list[Document]) -> dict:
        """生成回答 + 引用标注"""
        context_parts = []
        for i, doc in enumerate(context_docs):
            section = doc.metadata.get("section", "其他")
            content = doc.page_content
            context_parts.append(f"[{i+1}] ({section})\n{content}")

        context = "\n\n".join(context_parts)

        try:
            response = await self.llm.ainvoke(
                QA_PROMPT_TEMPLATE.format(context=context, question=query)
            )
            answer = llm_response_text(response)
        except Exception:
            logger.error("LLM生成回答失败", exc_info=True)
            return {"answer": "生成回答时出现问题，请稍后重试。", "references": []}

        # 回答表明简历中无相关信息时，不返回引用
        has_info = not any(marker in answer for marker in _NO_INFO_MARKERS)

        return {
            "answer": answer,
            "references": [
                {
                    "content": doc.page_content[:500],
                    "section": doc.metadata.get("section", "unknown"),
                }
                for doc in context_docs[:3]
            ] if has_info else [],
        }