"""Shared constants for long-term memory."""

from pathlib import Path

MEMORY_DB_PATH = str(
    Path(__file__).resolve().parents[2] / "db" / "agent_sessions" / "memory.db"
)

VALID_CATEGORIES = {"fact", "preference", "insight", "goal"}
CATEGORY_ORDER = ["fact", "preference", "insight", "goal"]
CATEGORY_LABELS = {"fact": "技能事实", "preference": "偏好", "insight": "洞察", "goal": "目标"}

DECAY_DAYS = {1: 7, 2: 30, 3: 90, 4: 180, 5: -1}

CONTEXT_MAX_CHARS = 520
CATEGORY_QUOTA = {"fact": 0.40, "preference": 0.30, "insight": 0.20, "goal": 0.10}

DOMAIN_MAP: dict[str, list[str]] = {
    "前端": ["react", "vue", "angular", "javascript", "typescript", "css", "html", "nextjs", "vite"],
    "后端": ["python", "java", "go", "fastapi", "django", "spring", "数据库", "redis", "kafka"],
    "简历": ["诊断", "优化", "项目", "教育", "工作经历", "匹配", "润色"],
    "面试": ["行为面试", "自我介绍", "八股文", "模拟", "评估"],
    "岗位": ["推荐", "职位", "招聘", "投递", "内推"],
    "薪资": ["年薪", "月薪", "待遇", "涨薪", "谈薪", "k"],
    "城市": ["北京", "上海", "深圳", "广州", "杭州", "成都", "远程"],
}

EXTRACTION_PROMPT = """你是长期记忆抽取器。请从对话中提取“关于用户且可跨会话复用”的信息。

已有记忆：
{existing_summary}

规则：
1) 只保留重要度>=3的信息（3=有参考价值，4=重要，5=核心）。
2) 同一事实若出现更新，使用 delete 标注旧 key，并在 upsert 给出新内容。
3) content 精炼，不超过 40 字，禁止把助手建议当成用户记忆。
4) fact/insight 通常 append；preference/goal 通常 overwrite。
5) 输出必须是 JSON，不要 markdown 代码块。

输出格式：
{{
  "upsert": [
    {{
      "category": "fact|preference|insight|goal",
      "mem_key": "snake_case_key",
      "content": "记忆内容",
      "importance": 3,
      "confidence": 0.85,
      "mode": "append|overwrite"
    }}
  ],
  "delete": ["category/mem_key", "mem_key_only"]
}}
"""

# Legacy alias used by extraction mixin
_EXTRACTION_PROMPT = EXTRACTION_PROMPT
