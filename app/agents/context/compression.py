"""History compression settings for long conversations."""

COMPRESSION_PROMPT = """参考日期（唯一权威，当前对话的「今天」）：{today}

把以下对话历史压缩为一段简洁摘要，保留关键信息（用户偏好、岗位需求、简历要点、最新诊断结论），丢弃寒暄和重复内容。

摘要规则：
- 不要写「当前是X年X月」「今天是X」等日期断言（参考日期已在上方给出）
- 时间相关表述用「之前」「上一轮」即可
- 若多轮诊断评分不同，只保留最新分数
- 不要复述系统注入的上下文前缀

对话：
{messages}

摘要："""

COMPRESSION_THRESHOLD = 30
