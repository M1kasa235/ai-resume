"""Supervisor Agent — 编排子 agent 实现多智能体协作，支持并行调用"""

import asyncio
import logging
from datetime import date

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from app.core.llm import get_chat_model
from app.core.context import get_current_user_id, get_trace_id
from app.agents.config import create_checkpointer, make_middleware
from app.agents.agent import get_career_agent
from app.agents.resume_agent import get_resume_agent
from app.agents.registry import AgentRegistry
from app.agents.trace import AgentTrace

logger = logging.getLogger(__name__)

_message_counter: dict[str, int] = {}  # thread_id → 轮数计数


async def _get_memory_context(uid: int, query: str = "") -> str:
    import time
    from app.agents.memory import MemoryService
    t0 = time.time()
    cache_hit = False

    if not query:
        cached = MemoryService.get_cached_context(uid)
        if cached is not None:
            cache_hit = True
            elapsed_ms = int((time.time() - t0) * 1000)
            tid = get_trace_id()
            logger.info(
                f"[trace={tid}] [记忆注入] user={uid} cache=hit latency={elapsed_ms}ms "
                f"len={len(cached)} query_aware=0"
            )
            return cached

    svc = MemoryService()
    ctx = await svc.format_context(uid, query)
    if ctx and not query:
        MemoryService.set_cached_context(uid, ctx)

    elapsed_ms = int((time.time() - t0) * 1000)
    total = await svc.count(uid)
    tid = get_trace_id()
    logger.info(
        f"[trace={tid}] [记忆注入] user={uid} cache={'hit' if cache_hit else 'miss'} "
        f"latency={elapsed_ms}ms len={len(ctx)} total={total} query_aware={bool(query)}"
    )
    return ctx

# ── 结构化透传标记 ──
PASSTHROUGH_START = "<!--PASSTHROUGH_START-->"
PASSTHROUGH_END = "<!--PASSTHROUGH_END-->"


SUB_AGENT_TIMEOUT = 45  # 子 agent 超时秒数


async def _invoke_agent(role: str, query: str, uid: int) -> str:
    """调用单个子 agent，返回回复文本。超时返回友好提示。"""
    agent = get_resume_agent() if role == "resume" else get_career_agent()
    thread_id = f"user_{uid}_{role}"
    today = date.today().isoformat()
    contextualized = f"[系统上下文：今天是 {today}]\n\n{query}"
    try:
        async with AgentTrace(f"{role}_agent"):
            result = await asyncio.wait_for(
                agent.ainvoke(
                    {"messages": [HumanMessage(content=contextualized)]},
                    {"configurable": {"thread_id": thread_id}},
                ),
                timeout=SUB_AGENT_TIMEOUT,
            )
        reply = result["messages"][-1].content
        if role == "resume" and _is_structured_query(query):
            reply = f"{PASSTHROUGH_START}\n{reply}\n{PASSTHROUGH_END}"
        return reply
    except asyncio.TimeoutError:
        logger.error(f"{role}_agent 超时 ({SUB_AGENT_TIMEOUT}s)")
        return f"[{role} 专家响应超时，请稍后重试或简化你的问题]"
    except Exception as e:
        logger.error(f"{role}_agent 调用失败: {e}")
        return f"[{role} 专家暂时不可用] {str(e)}"


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
    return await _invoke_agent("resume", query, get_current_user_id())


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
    return await _invoke_agent("career", query, get_current_user_id())


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
    uid = get_current_user_id()

    resume_task = _invoke_agent("resume", query, uid)
    career_task = _invoke_agent("career", query, uid)

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


_AUTO_TRIGGER_ROUNDS = 10  # 每 N 轮自动触发 memory agent


@tool
async def memory_agent_tool(query: str) -> str:
    """管理用户的长期记忆。当用户明确说"记住XXX"、"别忘了XXX"、"记一下XXX"时调用。

也可以主动调用：当对话中出现了值得长期记住的用户信息（偏好、简历事实、目标、
行为洞察），调用此工具让记忆管家分析并存储。"""
    from app.agents.memory_agent import run_memory_agent, set_memory_source
    uid = get_current_user_id()
    thread_id = f"user_{uid}_memory"
    set_memory_source("explicit")
    asyncio.create_task(run_memory_agent(query, thread_id))
    return "好的，我来整理一下记忆。"


async def _maybe_trigger_memory_agent(thread_id: str):
    """每 10 轮对话自动触发记忆管理（fire-and-forget）"""
    _message_counter[thread_id] = _message_counter.get(thread_id, 0) + 1
    if _message_counter[thread_id] >= _AUTO_TRIGGER_ROUNDS:
        _message_counter[thread_id] = 0
        from app.agents.memory_agent import run_memory_agent
        from app.agents.memory import MemoryService
        uid = get_current_user_id()
        try:
            # 清理过期记忆
            if uid:
                svc = MemoryService()
                await svc.decay(uid)
        except Exception:
            pass
        try:
            # 从 checkpoint 获取对话摘要
            checkpoint = create_checkpointer().get(
                {"configurable": {"thread_id": thread_id}}
            )
            summary = ""
            if checkpoint and checkpoint.get("channel_values"):
                messages = checkpoint["channel_values"].get("messages", [])
                recent = [m.content for m in messages[-20:] if hasattr(m, "content") and m.content]
                summary = "\n".join(recent[-10:])  # 取最近 10 条消息
            if summary:
                from app.agents.memory_agent import set_memory_source
                set_memory_source("auto")
                asyncio.create_task(
                    run_memory_agent(summary, f"{thread_id}_auto")
                )
        except Exception:
            pass  # 静默失败


def _is_structured_query(query: str) -> bool:
    """判断是否为结构化输出请求（诊断/优化/匹配应透传，不要浓缩）"""
    structured_keywords = ["诊断", "优化", "匹配", "评分", "修改简历", "改简历", "润色"]
    return any(kw in query for kw in structured_keywords)


supervisor_prompt = """你是一个 AI 求职助手的主管，统筹处理用户的求职和简历需求。

你有以下专家可供调用：

1. **resume_agent_tool** — 简历专家（简历诊断/优化/匹配/查询）
2. **career_agent_tool** — 求职顾问（搜岗位/薪资/推荐/行业资讯）
3. **both_agents_tool** — 并行同时调用简历专家和求职顾问
4. **memory_agent_tool** — 记忆管家（用户说"记住"时调用）

## 工具选择规则

| 用户意图 | 选择 |
|---------|------|
| 纯简历问题（诊断/优化/查询/匹配） | resume_agent_tool |
| 纯求职问题（搜岗位/薪资/推荐） | career_agent_tool |
| 跨领域需求（简历+岗位都要） | **both_agents_tool**（并行，更快） |
| 用户明确说"记住XXX"、"别忘了XXX" | memory_agent_tool |

跨领域判断标准：用户需求同时涉及「我的简历里有什么/怎么样」和「外面有什么岗位/市场如何」，用 both_agents_tool。

## 输出规则（非常重要）

### 结构化结果 → 原样透传
如果简历专家返回的内容被 `<!--PASSTHROUGH_START-->` 和 `<!--PASSTHROUGH_END-->` 包裹，你必须**原样输出**标记内的全部内容，不得删减、浓缩或改写（去掉标记符号本身）。标记之外的内容按需总结。

### 严禁输出原始数据
- **绝对禁止**在你的回复中输出 JSON、字典、列表等原始数据格式
- **绝对禁止**输出工具调用的原始返回内容（raw tool result）
- 工具返回的数据仅供你参考和整合，不要直接打印给用户
- 哪怕是"先展示原始数据再总结"也不行——只输出最终面向用户的回答

### 工具故障降级
- 一个专家返回错误或空结果时，不要直接把错误信息抛给用户
- career_agent_tool 失败 → 尝试 both_agents_tool
- resume_agent_tool 失败 → 尝试 both_agents_tool（并行调用至少另一方有结果）
- 降级后需向用户说明信息来源变化
- 两次降级均失败才告知用户"系统暂不可用，请稍后重试"

### 多轮对话深化
- 查看对话历史：如果上一轮已经返回了结果（岗位列表、简历诊断等），新问题是基于这些结果的追问
- 追问场景下优先基于已有结果回答，不要重复调用同一个工具获取相同数据
- 判断是否需要重新调用工具的标准：用户要求了全新信息，而非对已有结果的筛选/排序/展开

### 通用原则
- 你是协调者，不要自己编造简历内容或岗位数据
- 用简洁的要点组织回答，避免大量表格、emoji、分割线
- 不要重复输出专家的原始完整回复（结构化透传除外）
- 如果收到内容前缀是"用户输入包含……"，必须以第一人称视角回复
- both_agents_tool 的输出用 `---` 分隔两个专家的结果，请按各自规则处理"""


def get_supervisor():
    """懒加载 supervisor agent"""
    def _build():
        model = get_chat_model()
        return create_agent(
            model=model,
            tools=[resume_agent_tool, career_agent_tool, both_agents_tool, memory_agent_tool],
            system_prompt=supervisor_prompt,
            checkpointer=create_checkpointer(),
            middleware=make_middleware(model),
            name="supervisor",
        )
    return AgentRegistry.get_or_create("supervisor", _build)


async def supervisor_stream(prompt: str, thread_id: str):
    """流式调用 supervisor agent"""
    from langchain_core.messages import AIMessageChunk
    uid = get_current_user_id()
    tid = get_trace_id()
    logger.info(f"[trace={tid}] supervisor_stream start user={uid} prompt={prompt[:80]}")

    # Pre-process: 意图分类 + 记忆检索 + 历史压缩（StateGraph）
    try:
        from app.agents.pre_process import pre_process
        enriched = await pre_process(uid, thread_id, prompt)
    except Exception:
        # 降级：走旧注入路径
        memory_ctx = await _get_memory_context(uid, query=prompt)
        if memory_ctx:
            enriched = memory_ctx + "\n\n" + prompt
        else:
            enriched = prompt

    asyncio.create_task(_maybe_trigger_memory_agent(thread_id))

    message = HumanMessage(content=enriched)
    try:
        agent = get_supervisor()
        async with AgentTrace("supervisor"):
            async for chunk, metadata in agent.astream(
                {"messages": [message]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield chunk.content
    except Exception as e:
        tid = get_trace_id()
        logger.error(f"[trace={tid}] Supervisor 流式调用失败: {e}")
        yield f"处理失败：{str(e)}"