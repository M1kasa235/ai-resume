"""Supervisor LangChain tools delegating to specialist agents."""

import asyncio

from langchain_core.tools import tool

from app.agents.orchestration.sub_agent import invoke_sub_agent
from app.core.async_tasks import create_context_task
from app.core.context import require_current_user_id


@tool
async def resume_agent_tool(query: str) -> str:
    """处理简历相关的问题：查询简历内容、诊断简历、针对岗位优化简历、匹配岗位。

触发场景示例（按优先级）：
- "帮我分析/诊断一下我的简历"       → 简历诊断（结构化输出，评分+优劣势+建议）
- "针对这个XX岗位帮我优化简历"       → 简历优化（结构化输出，逐段对比+完整简历）
- "我和这个岗位匹配度怎么样"          → 岗位匹配（结构化输出，各维度评分+分析）
- "帮我把这段经历润色一下"           → 段落润色（传入段落类型和原文）
- "我的项目经验/技能/教育背景是什么"  → 简历查询（自然语言回答）

注意：诊断、优化、匹配这三种返回的是结构化分析结果，会按原样展示给用户，不会做二次浓缩。
如果用户需求同时涉及简历和求职（如"根据简历推荐岗位"），优先调用 both_agents_tool。"""
    return await invoke_sub_agent("resume", query, require_current_user_id())


@tool
async def career_agent_tool(query: str) -> str:
    """处理求职和面试相关问题：搜索岗位、分析薪资、个性化推荐、行业资讯、面试技巧。

触发场景示例（按优先级）：
- "帮我推荐/找一些XX岗位"           → 岗位推荐（基于用户画像）
- "XX岗位/XX城市薪资怎么样"          → 薪资分析
- "搜索/找一下XX的岗位"              → 岗位搜索
- "前端/后端开发的发展趋势"          → 行业资讯（搜网）
- "面试一般问什么/怎么准备面试"       → 面试技巧（知识库）

如果用户需求同时涉及简历和求职（如"根据简历推荐岗位"），优先调用 both_agents_tool。"""
    return await invoke_sub_agent("career", query, require_current_user_id())


@tool
async def both_agents_tool(query: str) -> str:
    """同时咨询简历专家和求职顾问，两个专家并行处理、合并返回。

适用场景（跨领域需求）：
- "帮我全面分析求职竞争力"              → 简历诊断 + 市场行情
- "根据我的简历推荐合适的岗位"           → 简历查询 + 岗位推荐
- "我适合投哪些公司"                   → 简历分析 + 岗位搜索
- "分析我的简历然后推荐匹配的岗位"        → 简历诊断 + 岗位推荐+匹配
- 任何同时涉及「简历本身」和「外部岗位市场」的复合需求

注意：本工具会并行调用两个专家，比逐个调用节省约一半时间。"""
    uid = require_current_user_id()
    resume_task = invoke_sub_agent("resume", query, uid)
    career_task = invoke_sub_agent("career", query, uid)
    resume_result, career_result = await asyncio.gather(
        resume_task, career_task, return_exceptions=True,
    )
    if isinstance(resume_result, Exception):
        resume_result = f"[简历专家不可用] {str(resume_result)}"
    if isinstance(career_result, Exception):
        career_result = f"[求职顾问不可用] {str(career_result)}"
    parts = []
    if resume_result and resume_result != "无相关信息":
        parts.append(resume_result)
    if career_result and career_result != "无相关信息":
        parts.append(career_result)
    return "\n\n---\n\n".join(parts) if parts else "两个专家均未返回有效结果"


@tool
async def memory_agent_tool(query: str) -> str:
    """管理用户的长期记忆。当用户明确说"记住XXX"、"别忘了XXX"、"记一下XXX"时调用。

也可以主动调用：当对话中出现了值得长期记住的用户信息（偏好、简历事实、目标、
行为洞察），调用此工具让记忆管家分析并存储。"""
    from app.agents.memory.ingest import run_memory_agent, set_memory_source

    uid = require_current_user_id()
    thread_id = f"user_{uid}_memory"
    set_memory_source("explicit")
    create_context_task(
        run_memory_agent(
            query,
            thread_id=thread_id,
            event_type="explicit_command",
            sync_process=False,
        )
    )
    return "好的，我来整理一下记忆。"


SUPERVISOR_TOOLS = [
    resume_agent_tool,
    career_agent_tool,
    both_agents_tool,
    memory_agent_tool,
]
