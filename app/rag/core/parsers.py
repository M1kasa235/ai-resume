"""共享结构化解析 — JSON / CSV 统一解析

所有知识库入库路径共用此模块，统一字段映射逻辑。
"""

import csv
import io
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# CSV/JSON 字段名映射（兼容中英文多种写法）
FIELD_MAP = {
    "title":         ["title", "标题", "岗位名称", "名称", "name", "职位"],
    "category":      ["category", "company", "分类", "公司", "企业"],
    "description":   ["description", "描述", "岗位描述", "工作职责", "职责", "内容"],
    "requirements":  ["requirements", "要求", "任职要求", "岗位要求", "技能要求", "需求"],
}


def resolve_record(record: dict, index: int = 0) -> dict:
    """将任意字段名的 record 统一归一化为标准字段"""
    resolved: dict[str, Optional[str]] = {
        "title": None,
        "category": None,
        "description": None,
        "requirements": None,
    }
    for std_field, aliases in FIELD_MAP.items():
        for alias in aliases:
            if alias in record:
                resolved[std_field] = str(record[alias]).strip()
                break
    # 用索引兜底 title
    if not resolved["title"]:
        resolved["title"] = f"知识条目_{index}"
    return resolved


def parse_json(text: str) -> list[dict]:
    """解析 JSON 文本，返回归一化后的记录列表"""
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("records", data.get("data", [data]))
    if not isinstance(data, list):
        raise ValueError("JSON 格式错误: 需要数组")
    return [resolve_record(r, i) for i, r in enumerate(data)]


def parse_csv(text: str) -> list[dict]:
    """解析 CSV 文本，返回归一化后的记录列表"""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV 格式错误: 缺少表头")
    return [resolve_record(row, i) for i, row in enumerate(reader)]