"""Single source of truth for agent temporal context."""

from __future__ import annotations

from datetime import date

SYSTEM_DATE_PREFIX = "[系统上下文：今天是 {today}]"

# Appended to prompts that reason about resume timelines / graduation / project dates.
TEMPORAL_REASONING_RULES = (
    "时间判断规则：\n"
    "1. 仅以「系统上下文」中的今天日期作为当前日期，不要使用训练数据中的默认年份。\n"
    "2. 对话历史摘要中的日期描述可能已过期，不要复述摘要里的「当前是X月」类表述。\n"
    "3. 项目/实习起止时间以简历原文为准；与今天日期比较后再判断是否合理。\n"
    "4. 同一问题若与上一轮结论冲突，以本轮工具返回的最新结果为准。"
)


def reference_date() -> str:
    return date.today().isoformat()


def system_date_block(today: str | None = None) -> str:
    return SYSTEM_DATE_PREFIX.format(today=today or reference_date())


def user_message_with_date(user_text: str, today: str | None = None) -> str:
    body = (user_text or "").strip()
    return f"{system_date_block(today)}\n\n{body}"
