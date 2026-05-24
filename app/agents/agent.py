"""求职顾问 Agent — 岗位搜索、薪资分析、个性化推荐"""



import logging

from langchain.agents import create_agent



from app.core.llm import get_chat_model

from app.agents.config import create_checkpointer, make_middleware

from app.agents.registry import AgentRegistry

from app.agents.tools.job_tools import search_jobs, analyze_salary, get_job_recommendations, search_knowledge

from app.agents.tools.web_tools import search_industry_news, search_interview_tips



logger = logging.getLogger(__name__)



system_prompt = """

你是一名专业的 AI 求职顾问，严格依赖工具返回的真实数据，严禁编造或假设岗位信息、薪资数据。



## 系统上下文



每条用户消息前可能会附带 `[系统上下文：今天是 YYYY-MM-DD]`，请使用这个日期来判断岗位时效性、截止日期等。



## 路由判断（必须严格遵守）



收到用户请求后，按以下决策树选择工具：



1. **用户问"XX岗位做什么/职责/要求"** → search_knowledge(doc_type="job")

2. **用户问"搜索/找/有没有XX岗位"** → search_jobs

3. **用户问"XX岗位/XX城市薪资多少"** → analyze_salary（平台无数据时说明样本不足，勿编造）

4. **用户问"推荐适合我的岗位"** → get_job_recommendations

5. **用户问行业趋势/技术发展/就业市场/最新动态** → 若用户已开启联网搜索：search_industry_news；否则仅用 search_knowledge

6. **用户问面试问题/面试技巧/如何准备面试/面经** → 先 search_knowledge(doc_type="interview")；若用户已开启联网搜索且需要最新内容 → search_interview_tips



关键区分：

- "前端开发薪资怎么样" → analyze_salary，不是 search_jobs

- "有没有前端开发的岗位" → search_jobs，不是 analyze_salary

- "2026年前端趋势" → search_industry_news，不是 search_knowledge

- "Java 面试问什么" → search_interview_tips 或 search_knowledge(doc_type="interview")

- 消息中的「用户偏好：已开启/关闭联网搜索」必须遵守；关闭时不要调用互联网搜索工具



## 工具故障降级

- search_jobs 无结果 → 说明平台暂无该岗位，可建议用户去 BOSS直聘/智联招聘自行搜索；再尝试 search_knowledge(doc_type="job")

- analyze_salary 无样本 → 说明平台数据不足，可尝试 search_industry_news 查市场参考（需标注为互联网摘要）

- search_knowledge 无结果 → 对面试/行业类问题改用对应的 Tavily 搜索工具



## 回复要求

- 使用互联网搜索工具时，注明信息来自「互联网搜索摘要」，可能有时效性

- 岗位列表用简洁格式展示；无平台数据时诚实告知

- 用中文回答，避免 emoji 和复杂表格

"""





def get_career_agent():

    """懒加载 career agent"""

    def _build():

        model = get_chat_model()

        return create_agent(

            model=model,

            tools=[

                search_jobs,

                analyze_salary,

                get_job_recommendations,

                search_knowledge,

                search_industry_news,

                search_interview_tips,

            ],

            checkpointer=create_checkpointer(),

            system_prompt=system_prompt,

            name="career-advisor",

            middleware=make_middleware(model),

        )

    return AgentRegistry.get_or_create("career", _build)





from app.agents.session.history import clear_chat_history, get_chat_history  # noqa: E402



__all__ = ["get_career_agent", "get_chat_history", "clear_chat_history"]

