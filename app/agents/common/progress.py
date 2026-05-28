"""Shared status labels for agent chat streaming UI."""

STATUS_UNDERSTAND = "正在理解您的问题…"
STATUS_ASSEMBLE_CONTEXT = "正在组装对话上下文…"
STATUS_COORDINATE = "正在协调专家处理…"
STATUS_GENERATE = "正在生成回复…"
STATUS_RESUME_DIAGNOSE = "正在诊断您的简历…"

TOOL_STATUS_LABELS: dict[str, str] = {
    "resume_agent_tool": "正在咨询简历专家…",
    "career_agent_tool": "正在咨询求职顾问…",
    "both_agents_tool": "正在并行咨询简历与求职专家…",
    "memory_agent_tool": "正在整理长期记忆…",
    "diagnose_resume": "正在全面诊断简历…",
    "query_resume": "正在检索简历内容…",
    "optimize_for_job": "正在针对岗位优化简历…",
    "match_resume_to_job": "正在分析岗位匹配度…",
    "polish_section": "正在润色简历段落…",
    "search_jobs": "正在搜索岗位…",
    "get_job": "正在获取岗位详情…",
    "search_knowledge": "正在检索知识库…",
    "analyze_salary": "正在分析薪资数据…",
    "get_job_recommendations": "正在生成岗位推荐…",
    "search_industry_news": "正在搜索行业资讯…",
    "search_interview_tips": "正在搜索面试技巧…",
    "search_resume_writing_tips": "正在搜索简历写作建议…",
}


def tool_status_message(tool_name: str) -> str:
    return TOOL_STATUS_LABELS.get(tool_name, f"正在调用 {tool_name}…")
