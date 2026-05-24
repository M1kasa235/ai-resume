PASSTHROUGH_START = "<!--PASSTHROUGH_START-->"
PASSTHROUGH_END = "<!--PASSTHROUGH_END-->"
SUB_AGENT_TIMEOUT = 45

STRUCTURED_KEYWORDS = ["诊断", "优化", "匹配", "评分", "修改简历", "改简历", "润色"]


def is_structured_query(query: str) -> bool:
    return any(kw in query for kw in STRUCTURED_KEYWORDS)
