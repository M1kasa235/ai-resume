"""Format structured resume tool outputs for user-facing display."""

from __future__ import annotations

import json
import re
from typing import Any


def format_diagnosis_report(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"诊断失败：{data['error']}"

    lines = [
        "## 简历诊断报告",
        f"**综合评分**：{data.get('overall_score', 'N/A')}",
        "",
    ]

    strengths = data.get("strengths") or []
    if strengths:
        lines.append("### 优势")
        for i, item in enumerate(strengths, 1):
            lines.append(f"{i}. {item}")
        lines.append("")

    weaknesses = data.get("weaknesses") or []
    if weaknesses:
        lines.append("### 不足")
        for i, item in enumerate(weaknesses, 1):
            lines.append(f"{i}. {item}")
        lines.append("")

    suggestions = data.get("suggestions") or []
    if suggestions:
        lines.append("### 改进建议")
        for i, item in enumerate(suggestions, 1):
            if isinstance(item, dict):
                section = item.get("section") or "通用"
                issue = item.get("issue") or ""
                advice = item.get("advice") or ""
                lines.append(f"{i}. **{section}**")
                if issue:
                    lines.append(f"   - 问题：{issue}")
                if advice:
                    lines.append(f"   - 建议：{advice}")
            else:
                lines.append(f"{i}. {item}")
        lines.append("")

    if data.get("raw_response"):
        lines.append(str(data["raw_response"]))

    return "\n".join(lines).strip()


def format_optimize_report(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"优化失败：{data['error']}"

    lines = ["## 简历优化结果", ""]
    summary = data.get("summary")
    if isinstance(summary, dict):
        before = summary.get("match_score_before")
        after = summary.get("match_score_after")
        if before is not None and after is not None:
            lines.append(f"**匹配度变化**：{before} → {after}")
            lines.append("")
        changes = summary.get("changes") or []
        if changes:
            lines.append("### 主要改动")
            for i, c in enumerate(changes, 1):
                lines.append(f"{i}. {c}")
            lines.append("")

    sections = data.get("optimized_sections") or []
    if sections:
        lines.append("### 逐段优化")
        for item in sections:
            if not isinstance(item, dict):
                continue
            section = item.get("section") or "段落"
            lines.append(f"#### {section}")
            if item.get("original"):
                lines.append(f"- 原文：{item['original']}")
            if item.get("optimized"):
                lines.append(f"- 优化：{item['optimized']}")
            if item.get("change_reason"):
                lines.append(f"- 原因：{item['change_reason']}")
            lines.append("")

    if data.get("full_resume"):
        lines.append("### 优化后完整简历")
        lines.append(str(data["full_resume"]))

    if data.get("raw_response"):
        lines.append(str(data["raw_response"]))

    return "\n".join(lines).strip() or json.dumps(data, ensure_ascii=False)


def format_match_report(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"匹配分析失败：{data['error']}"

    lines = ["## 岗位匹配分析", ""]
    if data.get("overall_score") is not None:
        lines.append(f"**整体匹配度**：{data['overall_score']}")
        lines.append("")

    dimensions = data.get("dimensions") or data.get("scores") or {}
    if isinstance(dimensions, dict) and dimensions:
        lines.append("### 各维度评分")
        for name, score in dimensions.items():
            lines.append(f"- {name}：{score}")
        lines.append("")

    for key, title in (
        ("analysis", "分析"),
        ("gaps", "差距"),
        ("recommendations", "建议"),
        ("summary", "总结"),
    ):
        value = data.get(key)
        if not value:
            continue
        lines.append(f"### {title}")
        if isinstance(value, list):
            for i, item in enumerate(value, 1):
                lines.append(f"{i}. {item}")
        else:
            lines.append(str(value))
        lines.append("")

    return "\n".join(lines).strip() or json.dumps(data, ensure_ascii=False)


def format_polish_report(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"润色失败：{data['error']}"

    lines = ["## 段落润色结果", ""]
    if data.get("original"):
        lines.append(f"**原文**\n{data['original']}\n")
    if data.get("optimized"):
        lines.append(f"**优化后**\n{data['optimized']}\n")
    if data.get("change_reason"):
        lines.append(f"**改动说明**：{data['change_reason']}")

    return "\n".join(lines).strip() or json.dumps(data, ensure_ascii=False)


def format_query_report(data: dict[str, Any]) -> str:
    if data.get("error"):
        return f"查询失败：{data['error']}"
    answer = data.get("answer") or data.get("content") or ""
    if answer:
        return str(answer).strip()
    return json.dumps(data, ensure_ascii=False)


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def strip_json_from_reply(reply: str) -> str:
    """If the model leaked raw JSON, replace it with formatted markdown."""
    text = (reply or "").strip()
    if not text or '"overall_score"' not in text:
        return text

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        return text

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return text

    if "overall_score" in data or "strengths" in data:
        formatted = format_diagnosis_report(data)
    elif "optimized_sections" in data or "full_resume" in data:
        formatted = format_optimize_report(data)
    elif "dimensions" in data or "overall_score" in data:
        formatted = format_match_report(data)
    else:
        return text

    prefix = text[: match.start()].strip()
    # Drop redundant filler before the report
    filler_markers = ("请稍等", "全面诊断", "我来看看", "好的，")
    if prefix and not any(m in prefix for m in filler_markers):
        return f"{prefix}\n\n{formatted}"
    return formatted
