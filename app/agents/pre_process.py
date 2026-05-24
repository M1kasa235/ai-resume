"""Pre-process — 预处理用户输入：意图分类 + 记忆检索 + 历史压缩

在 supervisor 之前运行，无流式输出，不影响现有链路。
"""

import time
import logging

from app.core.context import get_trace_id

logger = logging.getLogger(__name__)

# ── 规则意图分类（零延迟） ──

_JOB_WORDS = ["岗位", "推荐", "薪资", "搜索", "招聘", "职位", "内推", "投递", "行业", "趋势", "面试"]
_RESUME_WORDS = ["简历", "诊断", "优化", "匹配", "润色", "修改", "项目经验", "工作经历"]
_MEMORY_WORDS = ["记住", "记一下", "别忘了", "记录下来"]

_INTENT_CONFIG = {
    "job_search": {"needs_memory": True,  "priority_categories": ["preference", "fact"]},
    "resume":     {"needs_memory": True,  "priority_categories": ["fact", "insight"]},
    "hybrid":     {"needs_memory": True,  "priority_categories": ["fact", "preference"]},
    "memory":     {"needs_memory": False, "priority_categories": []},
    "chat":       {"needs_memory": False, "priority_categories": []},
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


# ── 历史压缩 ──

COMPRESSION_PROMPT = """把以下对话历史压缩为一段简洁摘要，保留关键信息（用户偏好、岗位需求、简历要点），丢弃寒暄和重复内容。

对话：
{messages}

摘要："""

COMPRESSION_THRESHOLD = 30


async def assemble_context(user_id: int, thread_id: str, message: str):
    """Build structured ContextBundle for the current turn."""
    from app.agents.context_assembler import assemble_context as _assemble

    return await _assemble(user_id, thread_id, message)


async def pre_process(user_id: int, thread_id: str, message: str) -> str:
    """预处理用户消息，返回 enriched prompt（兼容旧接口）。"""
    t0 = time.time()
    bundle = await assemble_context(user_id, thread_id, message)
    enriched = bundle.render()
    meta = bundle.to_log_dict()
    elapsed = int((time.time() - t0) * 1000)
    logger.info(
        "[trace=%s] pre_process done %sms intent=%s blocks=%s truncated=%s",
        get_trace_id(),
        elapsed,
        meta.get("intent"),
        len(meta.get("blocks", [])),
        meta.get("truncated"),
    )
    return enriched
