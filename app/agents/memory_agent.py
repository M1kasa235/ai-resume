"""Memory Agent — 长期记忆管家，自主判断增/改/删"""

import json
import logging
import asyncio
import contextvars

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from app.core.llm import get_chat_model
from app.core.context import get_trace_id, require_current_user_id
from app.agents.config import create_checkpointer, make_middleware
from app.agents.registry import AgentRegistry
from app.agents.trace import AgentTrace
from app.agents.memory import MemoryService

logger = logging.getLogger(__name__)

# 记忆写入来源标记（contextvar 穿透 asyncio.create_task）
_memory_source: contextvars.ContextVar[str] = contextvars.ContextVar(
    "memory_source", default="unknown"
)


def set_memory_source(source: str):
    _memory_source.set(source)


# ═══════ 工具 ═══════

@tool
async def list_memories() -> str:
    """查看当前用户的所有长期记忆，返回 JSON 列表。
在决定新增或更新记忆前，先调用此工具了解已有记忆，避免重复。"""
    uid = require_current_user_id()
    memories = await MemoryService().get_all(uid)
    return json.dumps(memories, ensure_ascii=False, default=str)


@tool
async def upsert_memory(
    category: str, mem_key: str, content: str, importance: int = 3,
    mode: str = "overwrite",
) -> str:
    """新增或更新一条记忆。

参数：
- category: fact / preference / insight / goal
- mem_key: 简短英文标识，如 "skill_react", "target_city"
- content: 简洁中文描述，不超过 30 字
- importance: 1-5 (5=核心事实, 4=重要, 3=有参考价值)
- mode: "overwrite"（覆盖型，同key更新）| "append"（累加型，自动生成唯一key不覆盖）

注意：fact 和 insight 用 append，preference 和 goal 用 overwrite。"""
    from datetime import datetime
    uid = require_current_user_id()
    if mode == "append":
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        mem_key = f"{mem_key}_{ts}"
    source = _memory_source.get()
    await MemoryService().upsert(uid, category, mem_key, content, importance, source)
    MemoryService.invalidate_cache(uid)
    tid = get_trace_id()
    logger.info(f"[trace={tid}] memory_agent upsert: user={uid} {category}/{mem_key} mode={mode} src={source}")
    return f"已记忆 [{category}] {mem_key}: {content}"


@tool
async def delete_memory(category: str, mem_key: str) -> str:
    """删除一条过时的记忆。

参数：
- category: 记忆类别
- mem_key: 要删除的记忆标识"""
    uid = require_current_user_id()
    await MemoryService().delete(uid, category, mem_key)
    MemoryService.invalidate_cache(uid)
    tid = get_trace_id()
    logger.info(f"[trace={tid}] memory_agent delete: user={uid} {category}/{mem_key}")
    return f"已删除 [{category}] {mem_key}"


# ═══════ System Prompt ═══════

SYSTEM_PROMPT = """你是用户的长期记忆管家。你会收到一段对话历史摘要，请判断哪些信息值得长期记住。

## 操作流程
1. 先调用 list_memories 查看已有记忆
2. 分析对话摘要，判断：
   - 新增：新出现的偏好、事实、目标、洞察
   - 更新：已有信息被覆盖（如薪资期望从"20k"变成"25k"）
   - 删除：已过时的临时信息（如面试已结束、目标已达成）
3. 调用 upsert_memory / delete_memory 执行变更

## 该记的
- 用户偏好：目标城市、薪资范围、岗位类型、行业偏好
- 简历事实：技能、经验年限、项目、教育背景
- 行为洞察：面试弱项、擅长领域
- 阶段性目标：投递计划、跳槽时间

## 不该记的
- 闲聊寒暄、问候
- 每次对话都重复且未变化的信息
- 已有记忆中完全一致的内容
- AI 给用户的建议（那是给用户的，不是关于用户的）

## 记忆格式
- category: fact / preference / insight / goal
- mem_key: 简短英文标识，下划线分隔
- content: ≤30字中文
- importance: 5=核心身份(永远不会忘) 4=重要 3=有参考价值

## 更新原则
- 同 mem_key 直接 upsert 覆盖，不会重复
- 内容有实质变化才更新，完全相同则跳过
- 临时的阶段性信息（如"正在准备XX面试"）面试结束后调用 delete_memory 删除
- 无重要变化时不需要任何操作

## mode 选择（重要）
- fact（硬事实）→ mode="append"：技能、公司、项目、教育经历等是累加的，每条用不同 key
- insight（洞察）→ mode="append"：每次诊断/面试的发现独立保留，不覆盖
- preference（偏好）→ mode="overwrite"：城市、薪资、岗位类型偏好在变化时覆盖
- goal（目标）→ mode="overwrite"：当前目标变了旧的就无效，直接覆盖"""


# ═══════ Agent ═══════

def get_memory_agent():
    """懒加载 memory agent"""
    def _build():
        model = get_chat_model()
        return create_agent(
            model=model,
            tools=[list_memories, upsert_memory, delete_memory],
            system_prompt=SYSTEM_PROMPT,
            checkpointer=create_checkpointer(),
            middleware=make_middleware(model),
            name="memory-agent",
        )
    return AgentRegistry.get_or_create("memory", _build)


async def run_memory_agent(dialogue_summary: str, thread_id: str = "memory"):
    """调用 memory agent 分析对话并管理记忆

    使用独立 thread_id 避免与对话 thread 混淆。
    静默失败，不影响主流程。
    """
    try:
        agent = get_memory_agent()
        async with AgentTrace("memory_agent"):
            await asyncio.wait_for(
                agent.ainvoke(
                    {"messages": [HumanMessage(content=dialogue_summary)]},
                    {"configurable": {"thread_id": thread_id}},
                ),
                timeout=45,
            )
    except asyncio.TimeoutError:
        logger.warning("memory agent 超时")
    except Exception:
        logger.warning("memory agent 调用失败", exc_info=True)
