"""History compression settings for long conversations."""

COMPRESSION_PROMPT = """把以下对话历史压缩为一段简洁摘要，保留关键信息（用户偏好、岗位需求、简历要点），丢弃寒暄和重复内容。

对话：
{messages}

摘要："""

COMPRESSION_THRESHOLD = 30
