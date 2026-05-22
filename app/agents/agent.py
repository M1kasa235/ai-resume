"""求职顾问 Agent — 岗位搜索、薪资分析、个性化推荐"""

import logging
from langchain_core.messages import AIMessage
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

from app.core.llm import get_chat_model
from app.core.config import settings
from app.core.context import get_trace_id
from app.agents.config import create_checkpointer, make_middleware
from app.agents.registry import AgentRegistry
from app.agents.tools.job_tools import search_jobs, analyze_salary, get_job_recommendations, search_knowledge

logger = logging.getLogger(__name__)

tavily = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=settings.TAVILY_API_KEY,
)

system_prompt = """
你是一名专业的 AI 求职顾问，严格依赖工具返回的真实数据，严禁编造或假设岗位信息、薪资数据。

## 系统上下文

每条用户消息前可能会附带 `[系统上下文：今天是 YYYY-MM-DD]`，请使用这个日期来判断岗位时效性、截止日期等。

## 路由判断（必须严格遵守）

收到用户请求后，按以下决策树选择工具：

1. **用户问"XX岗位做什么/职责/要求"** → search_knowledge(doc_type="job")，从知识库检索岗位详情
2. **用户问"搜索/找/有没有XX岗位"** → search_jobs，按关键字/城市/薪资过滤
3. **用户问"XX岗位/XX城市薪资多少"** → analyze_salary，分析薪资水平
4. **用户问"推荐适合我的岗位"** → get_job_recommendations，基于用户画像推荐
5. **用户问"行业趋势/技术发展/最新动态"** → tavily_search（web_search），搜互联网资讯
6. **用户问"面试问题/面试技巧/如何准备面试/面试注意什么"** → search_knowledge(doc_type="interview")，从知识库检索面试经验

关键区分：
- "前端开发薪资怎么样" → analyze_salary（薪资分析），不是 search_jobs
- "有没有前端开发的岗位" → search_jobs（岗位搜索），不是 analyze_salary
- "帮我推荐岗位" → get_job_recommendations（个性化推荐），不是 search_jobs
- "前端开发是什么/需要什么技能" → search_knowledge（知识库），不是 web_search
- "2026年前端趋势" → web_search（时效性资讯），不是 search_knowledge
- "面试一般问什么问题/怎么准备面试" → search_knowledge(doc_type="interview")，不是 web_search

## 工具故障降级
- search_jobs 失败或返回空时，自动尝试 search_knowledge(doc_type="job") 获取相关岗位信息
- analyze_salary 失败时，尝试 search_knowledge 或 web_search 查找薪资参考
- 两次降级均失败才告知用户"暂未找到相关信息"
- 降级后需说明信息来源变化

## 回复要求
- 基于工具返回的真实数据回答，工具搜不到才能用自己的知识补充（需标注"以下为通用建议"）
- 岗位列表用简洁格式展示，每条包含：岗位名、公司、城市、薪资范围
- 如有多个结果，按匹配度或薪资从高到低排列
- 用中文回答，避免 emoji 和复杂表格
"""


def get_career_agent():
    """懒加载 career agent"""
    def _build():
        model = get_chat_model()
        return create_agent(
            model=model,
            tools=[tavily, search_jobs, analyze_salary, get_job_recommendations, search_knowledge],
            checkpointer=create_checkpointer(),
            system_prompt=system_prompt,
            name="career-advisor",
            middleware=make_middleware(model),
        )
    return AgentRegistry.get_or_create("career", _build)


def get_chat_history(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    logger.info(f"获取历史消息，thread_id: {thread_id}")
    checkpoint = _ensure_checkpointer().get({"configurable": {"thread_id": thread_id}})
    if not checkpoint:
        return []
    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []
    messages = channel_values.get("messages", [])
    if not messages:
        return []
    result = []
    for msg in messages:
        if not msg.content:
            continue
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
    return result


def clear_chat_history(thread_id: str):
    """清空会话"""
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    _ensure_checkpointer().delete_thread(thread_id)