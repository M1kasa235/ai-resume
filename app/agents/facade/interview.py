"""Public API for AI mock interview sessions."""

import logging

from langchain_core.messages import HumanMessage

from app.agents.common.errors import agent_stream_error_message
from app.agents.common.run_config import agent_run_config
from app.agents.common.streaming import extract_stream_text
from app.agents.factories.interview import get_interview_agent
from app.agents.prompts.interview import (
    INTERVIEW_TYPE_INTROS,
    INTERVIEW_TYPE_LABELS,
)

logger = logging.getLogger(__name__)


async def conduct_interview(prompt: str, thread_id: str) -> str:
    """调用面试官 agent，返回 AI 回复"""
    agent = get_interview_agent()
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            agent_run_config(thread_id),
        )
        return result["messages"][-1].content
    except Exception as exc:
        logger.error("interview agent invoke failed: %s", exc, exc_info=True)
        return agent_stream_error_message(exc)


async def conduct_interview_stream(prompt: str, thread_id: str):
    """流式调用面试官 agent，逐 token 返回"""
    agent = get_interview_agent()
    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=prompt)]},
            agent_run_config(thread_id),
            version="v2",
        ):
            if event.get("event") != "on_chat_model_stream":
                continue
            text = extract_stream_text(event.get("data", {}).get("chunk"))
            if text:
                yield text
    except Exception as exc:
        logger.error("interview agent stream failed: %s", exc, exc_info=True)
        yield agent_stream_error_message(exc)


def build_initial_prompt(
    interview_type: str,
    job_title: str,
    company_name: str,
    job_description: str = "",
    resume_text: str = "",
) -> str:
    """构建面试开场提示词（按类型差异化，简历已预查好）"""
    type_intro = INTERVIEW_TYPE_INTROS.get(
        interview_type, INTERVIEW_TYPE_INTROS["comprehensive"]
    )
    company_info = f"目标公司：{company_name}。" if company_name else ""
    jd_info = f"岗位 JD：\n{job_description}\n" if job_description else ""
    resume_info = f"候选人简历概要：\n{resume_text}\n" if resume_text else ""

    return (
        f"{type_intro}\n"
        f"目标岗位：{job_title or '未指定'}。{company_info}\n"
        f"{jd_info}"
        f"{resume_info}"
        f"面试预计进行约 20 个问题，请合理覆盖各维度。\n"
        f"候选人简历已在上面提供，请基于简历内容和岗位要求直接开始面试。\n"
        f"先做简短的开场白，然后请候选人做自我介绍。\n"
        f"如果提供了岗位 JD，务必基于 JD 中的技术要求、职责描述来出题。"
    )


def build_evaluation_prompt(transcript: str, interview_type: str) -> str:
    """构建评估提示词"""
    type_name = INTERVIEW_TYPE_LABELS.get(interview_type, "面试")
    return (
        f"模拟面试已经结束。以下是本次{type_name}的完整记录：\n\n"
        f"{transcript}\n\n"
        f"请作为面试官对候选人的表现进行全面评估。严格按以下 Markdown 格式输出，不要遗漏任何一题：\n\n"
        f"# AI 模拟面试评估报告\n\n"
        f"**面试类型：** {type_name} | **题目数量：** [填写] 题 | **综合评分：** [0-100]\n\n"
        f"---\n\n"
        f"## 逐题评估\n\n"
        f"（务必为每一道题生成以下内容）\n\n"
        f"### Q1: [AI 的提问原文]\n"
        f"**你的回答：** [候选人的回答原文，可适当精简但保留要点]\n"
        f"**评分：** [1-10]/10\n"
        f"**点评：** [具体点评，指出亮点和不足]\n"
        f"**参考回答：** [提供更好的回答思路或标准答案要点]\n\n"
        f"### Q2: [AI 的提问原文]\n"
        f"...（依此类推，务必覆盖全部题目）\n\n"
        f"---\n\n"
        f"## 综合评估\n\n"
        f"### 优势分析\n"
        f"- [列出 2-4 个具体优势，需结合面试中的实际表现举例]\n\n"
        f"### 待改进点\n"
        f"- [列出 2-4 个需要改进的地方，需结合面试中的具体表现举例]\n\n"
        f"### 改进建议\n"
        f"1. [具体可行的建议1]\n"
        f"2. [具体可行的建议2]\n"
        f"3. [具体可行的建议3]\n"
    )


__all__ = [
    "get_interview_agent",
    "conduct_interview",
    "conduct_interview_stream",
    "build_initial_prompt",
    "build_evaluation_prompt",
]
