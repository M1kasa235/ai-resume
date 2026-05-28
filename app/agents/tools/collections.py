"""Canonical tool lists per agent role.

Career advisor: job search, salary, recommendations, knowledge, web search.
Resume expert: resume RAG + search_jobs/get_job for match/optimize workflows.
Interview: knowledge + resume Q&A only.
"""

from app.agents.tools.job_tools import (
    analyze_salary,
    get_job,
    get_job_recommendations,
    search_jobs,
    search_knowledge,
)
from app.agents.tools.resume_tools import (
    diagnose_resume,
    match_resume_to_job,
    optimize_for_job,
    polish_section,
    query_resume,
)
from app.agents.tools.web_tools import (
    search_industry_news,
    search_interview_tips,
    search_resume_writing_tips,
)

CAREER_TOOLS = [
    search_jobs,
    get_job,
    analyze_salary,
    get_job_recommendations,
    search_knowledge,
    search_industry_news,
    search_interview_tips,
]

RESUME_TOOLS = [
    search_jobs,
    get_job,
    search_knowledge,
    search_resume_writing_tips,
    search_interview_tips,
    query_resume,
    diagnose_resume,
    optimize_for_job,
    match_resume_to_job,
    polish_section,
]

INTERVIEW_TOOLS = [
    search_knowledge,
    query_resume,
]
