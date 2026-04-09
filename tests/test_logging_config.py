from __future__ import annotations

import json
import logging

import pytest

from python_framework.logging_config import configure_logging


def test_configure_logging_plain_when_forced(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHON_FRAMEWORK_PLAIN_LOG", "1")
    configure_logging("INFO", json_format=False)
    logging.getLogger("python_framework.probe").info("probe-plain")
    err = capsys.readouterr().err
    assert "INFO" in err and "probe-plain" in err


def test_configure_logging_json_emits_object(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", json_format=True)
    logging.getLogger("python_framework.test").info("probe")
    out = capsys.readouterr().out
    line = next(x for x in out.splitlines() if x.strip())
    data = json.loads(line)
    assert data["level"] == "INFO"
    assert data["message"] == "probe"
