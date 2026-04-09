from __future__ import annotations

import os

import pytest

from python_framework.config import Settings


def _clear_framework_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("PYTHON_FRAMEWORK_"):
            monkeypatch.delenv(key, raising=False)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_framework_env(monkeypatch)
    s = Settings()
    assert s.app_name == "python-framework"
    assert s.debug is False


def test_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_framework_env(monkeypatch)
    monkeypatch.setenv("PYTHON_FRAMEWORK_APP_NAME", "custom")
    monkeypatch.setenv("PYTHON_FRAMEWORK_DEBUG", "1")
    s = Settings()
    assert s.app_name == "custom"
    assert s.debug is True
