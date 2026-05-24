"""Rule-based intent classification for turn context."""

_JOB_WORDS = ["岗位", "推荐", "薪资", "搜索", "招聘", "职位", "内推", "投递", "行业", "趋势", "面试"]
_RESUME_WORDS = ["简历", "诊断", "优化", "匹配", "润色", "修改", "项目经验", "工作经历"]
_MEMORY_WORDS = ["记住", "记一下", "别忘了", "记录下来"]

_INTENT_CONFIG = {
    "job_search": {"needs_memory": True, "priority_categories": ["preference", "fact"]},
    "resume": {"needs_memory": True, "priority_categories": ["fact", "insight"]},
    "hybrid": {"needs_memory": True, "priority_categories": ["fact", "preference"]},
    "memory": {"needs_memory": False, "priority_categories": []},
    "chat": {"needs_memory": False, "priority_categories": []},
}


def classify_intent(message: str) -> dict:
    """规则匹配意图分类，零延迟"""
    msg = message.strip()
    if not msg:
        return {"category": "chat", "needs_memory": False, "priority_categories": []}

    match_job = any(w in msg for w in _JOB_WORDS)
    match_resume = any(w in msg for w in _RESUME_WORDS)
    match_memory = any(w in msg for w in _MEMORY_WORDS)

    if match_memory:
        category = "memory"
    elif match_job and match_resume:
        category = "hybrid"
    elif match_job:
        category = "job_search"
    elif match_resume:
        category = "resume"
    else:
        category = "chat"

    config = _INTENT_CONFIG[category]
    return {"category": category, **config}
