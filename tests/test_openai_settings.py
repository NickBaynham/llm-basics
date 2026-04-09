from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from python_framework.openai_settings import OpenAISettings


def _clear_openai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)


def test_openai_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-custom")
    s = OpenAISettings()
    assert s.api_key == "sk-test"
    assert s.model == "gpt-custom"


def test_openai_settings_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    s = OpenAISettings()
    assert s.model == "gpt-4.1-mini"


def test_openai_settings_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_openai_env(monkeypatch)
    with pytest.raises(ValidationError):
        OpenAISettings()


def test_openai_settings_empty_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "  ")
    with pytest.raises(ValidationError):
        OpenAISettings()


def test_openai_settings_case_env_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env lookup must be case-sensitive for OPENAI_* (standard on Unix)."""
    _clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    if "openai_api_key" in os.environ:
        monkeypatch.delenv("openai_api_key", raising=False)
    s = OpenAISettings()
    assert s.api_key == "sk-x"
