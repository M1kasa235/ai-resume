"""Tests for agent SSE error sanitization."""

from app.agents.common.errors import agent_stream_error_message


def test_agent_stream_error_debug(monkeypatch):
    monkeypatch.setattr("app.agents.common.errors.settings.DEBUG", True)
    msg = agent_stream_error_message(RuntimeError("secret api key"))
    assert "secret api key" in msg


def test_agent_stream_error_production(monkeypatch):
    monkeypatch.setattr("app.agents.common.errors.settings.DEBUG", False)
    msg = agent_stream_error_message(RuntimeError("secret api key"))
    assert "secret" not in msg
    assert "请稍后重试" in msg
