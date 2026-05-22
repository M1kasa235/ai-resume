"""Interviewer Agent — AI 模拟面试官，支持技术面/HR面/综合面，简历驱动个性化提问"""

import logging
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from app.core.llm import get_chat_model
from app.agents.config import create_checkpointer, make_middleware
from app.agents.registry import AgentRegistry
from app.agents.tools.job_tools import search_knowledge
from app.agents.tools.resume_tools import query_resume

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 Offer Pilot 的 AI 面试官，进行真实、深入的模拟面试。

## 核心规则
1. 每轮只问一个问题，等用户回答后再继续，禁止一次问多个
2. 基于简历提问，深入追问项目细节和技术决策，不问泛泛的通用题
3. 每题先给 1-2 句具体点评，再基于回答内容追问，不跳话题
4. 需要标准面试题时用 search_knowledge 工具（doc_type="interview"）
5. 约 20 题后自然结束，说"面试到这里就差不多了，感谢你的参与"
6. 口语化中文交流，不用序号、表格、emoji、分割线

## 面试类型
- technical: 技术深度、项目架构、系统设计、编码规范
- hr: 职业规划、团队协作、沟通表达、文化匹配、自我认知
- comprehensive: 技术+行为全覆盖，动态调整侧重点"""
_type_prompts = {
    "technical": (
        "你是一位资深技术面试官，正在进行技术面试。考察重点：技术深度、项目架构、系统设计、编码规范。"
    ),
    "hr": (
        "你是一位专业 HR 面试官，正在进行 HR 面试。考察重点：职业规划、团队协作、沟通表达、文化匹配。"
    ),
    "comprehensive": (
        "你是一位综合面试官，正在进行综合面试。技术能力与综合素质并重，根据对话走向动态调整侧重点。"
    ),
}


def get_interview_agent():
    """懒加载面试官 agent"""
    def _build():
        model = get_chat_model()
        return create_agent(
            model=model,
            tools=[search_knowledge, query_resume],
            system_prompt=SYSTEM_PROMPT,
            name="interviewer",
            checkpointer=create_checkpointer(),
            middleware=make_middleware(model),
        )
    return AgentRegistry.get_or_create("interview", _build)


async def conduct_interview(prompt: str, thread_id: str) -> str:
    """调用面试官 agent，返回 AI 回复"""
    agent = get_interview_agent()
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content


async def conduct_interview_stream(prompt: str, thread_id: str):
    """流式调用面试官 agent，逐 token 返回"""
    agent = get_interview_agent()
    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=prompt)]},
        {"configurable": {"thread_id": thread_id}},
        version="v2",
    ):
        if event.get("event") == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content


def build_initial_prompt(interview_type: str, job_title: str, company_name: str, job_description: str = "", resume_text: str = "") -> str:
    """构建面试开场提示词（按类型差异化，简历已预查好）"""
    type_name = {"technical": "技术面试", "hr": "HR 面试", "comprehensive": "综合面试"}
    type_intro = _type_prompts.get(interview_type, _type_prompts["comprehensive"])

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
    type_name = {"technical": "技术面试", "hr": "HR 面试", "comprehensive": "综合面试"}
    return (
        f"模拟面试已经结束。以下是本次{type_name.get(interview_type, '面试')}的完整记录：\n\n"
        f"{transcript}\n\n"
        f"请作为面试官对候选人的表现进行全面评估。严格按以下 Markdown 格式输出，不要遗漏任何一题：\n\n"
        f"# AI 模拟面试评估报告\n\n"
        f"**面试类型：** {type_name.get(interview_type, '面试')} | **题目数量：** [填写] 题 | **综合评分：** [0-100]\n\n"
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
