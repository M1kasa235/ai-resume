"""Tests for job tool formatting helpers."""

from types import SimpleNamespace

from app.services.job_lookup import (
    MSG_JOBS_EMPTY,
    format_education,
    format_job_detail,
    format_job_list,
    format_job_list_item,
    format_salary_range,
)


def _job(**kwargs):
    defaults = {
        "id": 42,
        "title": "Python 后端工程师",
        "company_name": "示例科技",
        "city": "上海",
        "salary_min": 20,
        "salary_max": 35,
        "education_requirement": "bachelor",
        "description": "负责后端开发",
        "requirements": "熟悉 Python",
        "is_active": True,
        "experience_display": "3-5年",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_format_job_list_item_includes_id():
    line = format_job_list_item(_job())
    assert "[id=42]" in line
    assert "Python 后端工程师" in line
    assert "示例科技" in line


def test_format_job_list_appends_id_hint():
    text = format_job_list([_job()], header="共 1 个：")
    assert "[id=42]" in text
    assert "match_resume_to_job" in text


def test_format_job_list_empty():
    assert format_job_list([]) == MSG_JOBS_EMPTY


def test_format_job_detail_includes_sections():
    text = format_job_detail(_job())
    assert "[id=42]" in text
    assert "### 职位描述" in text
    assert "### 岗位要求" in text


def test_format_education_maps_unlimited():
    assert format_education("unlimited") == "不限"
    assert format_education("bachelor") == "本科"


def test_format_salary_range_from_fields():
    assert "20-35k" in format_salary_range(_job())
