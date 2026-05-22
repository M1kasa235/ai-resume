"""RAG 通用工具函数"""

import json
import re
from typing import Any


def parse_json_from_llm(text: str) -> dict | None:
    """从 LLM 响应中提取并解析 JSON（兼容各种格式包裹）"""
    try:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def llm_response_text(resp: Any) -> str:
    """统一提取 LLM 响应文本"""
    return resp.content if hasattr(resp, "content") else str(resp)