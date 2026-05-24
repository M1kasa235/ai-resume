"""Pre-process — 预处理用户输入：意图分类 + 记忆检索 + 历史压缩

在 supervisor 之前运行，无流式输出，不影响现有链路。
"""

import time
import logging

from app.core.llm import get_chat_model

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


# ── 对外接口 ──

async def pre_process(user_id: int, thread_id: str, message: str) -> str:
    """预处理用户消息，返回 enriched prompt"""
    t0 = time.time()
    parts: list[str] = []

    # 1. 意图分类
    intent = classify_intent(message)

    # 2. 按意图定向检索记忆
    if intent.get("needs_memory"):
        try:
            from app.agents.memory import MemoryService
            svc = MemoryService()
            result = await svc.retrieve_for_injection(
                user_id=user_id,
                query=message,
                category_priority=intent.get("priority_categories", []),
            )
            ctx = result.get("text", "")
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.warning(f"记忆检索失败: {e}")

    # 3. 长对话时压缩历史
    try:
        from app.agents.config import create_checkpointer
        cp = create_checkpointer()
        checkpoint = cp.get({"configurable": {"thread_id": thread_id}})
        if checkpoint and checkpoint.get("channel_values"):
            messages = checkpoint["channel_values"].get("messages", [])
            if len(messages) > COMPRESSION_THRESHOLD:
                recent = [m.content for m in messages[-20:] if hasattr(m, "content") and m.content]
                if recent:
                    conversation = "\n".join(recent[-10:])
                    model = get_chat_model()
                    resp = await model.ainvoke(COMPRESSION_PROMPT.format(messages=conversation))
                    summary = resp.content if hasattr(resp, "content") else str(resp)
                    if summary.strip():
                        parts.insert(0, f"[对话历史摘要] {summary.strip()}")
    except Exception as e:
        logger.warning(f"历史压缩失败: {e}")

    # 4. 拼装
    parts.append(message)
    enriched = "\n\n".join(parts)

    from app.core.context import get_trace_id
    elapsed = int((time.time() - t0) * 1000)
    mem_len = len(parts[0]) if intent.get("needs_memory") and len(parts) > 1 else 0
    logger.info(
        f"[trace={get_trace_id()}] pre_process done {elapsed}ms "
        f"intent={intent.get('category')} mem_len={mem_len}"
    )

    return enriched
