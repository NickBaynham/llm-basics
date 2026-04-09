from __future__ import annotations

from python_framework.config import Settings


def test_settings_defaults() -> None:
    s = Settings.from_environ({})
    assert s.app_name == "python-framework"
    assert s.debug is False


def test_settings_from_environ() -> None:
    s = Settings.from_environ(
        {
            "PYTHON_FRAMEWORK_APP_NAME": "custom",
            "PYTHON_FRAMEWORK_DEBUG": "1",
        }
    )
    assert s.app_name == "custom"
    assert s.debug is True
