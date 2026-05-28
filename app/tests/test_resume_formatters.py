"""Tests for resume reply normalization."""

from app.agents.tools.resume_formatters import (
    extract_passthrough,
    normalize_structured_reply,
    strip_json_from_reply,
)


SAMPLE_JSON = """好的，我来对您的简历进行全面诊断分析！
```json
{
  "overall_score": "7/10",
  "strengths": ["优势一"],
  "weaknesses": ["不足一"],
  "suggestions": [{"section": "结构", "issue": "重复", "advice": "删除重复"}]
}
```

## 简历诊断报告
**综合评分**：7/10

### 优势
1. 优势一
"""


def test_strip_json_when_markdown_present():
    result = strip_json_from_reply(SAMPLE_JSON)
    assert "```json" not in result
    assert '"overall_score"' not in result
    assert "## 简历诊断报告" in result
    assert not result.startswith("好的")


def test_normalize_removes_duplicate_reports():
    duplicate = (
        "## 简历诊断报告\n**综合评分**：7/10\n\n### 优势\n1. A\n\n"
        "## 简历诊断报告\n**综合评分**：7/10\n\n### 优势\n1. A\n\n### 不足\n1. B\n"
    )
    result = normalize_structured_reply(duplicate)
    assert result.count("## 简历诊断报告") == 1
    assert "### 不足" in result


def test_extract_passthrough():
    wrapped = "<!--PASSTHROUGH_START-->\n报告正文\n<!--PASSTHROUGH_END-->"
    assert extract_passthrough(wrapped) == "报告正文"
