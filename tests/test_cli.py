from __future__ import annotations

import json

import pytest

from python_framework.cli import build_parser, main


def test_build_parser_has_subcommands() -> None:
    parser = build_parser()
    subs = {action.dest: action for action in parser._actions if hasattr(action, "choices")}
    assert "command" in subs
    choices = subs["command"].choices
    assert choices is not None
    assert set(choices) >= {"hello", "ping", "config"}


def test_hello_default(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["hello"])
    assert code == 0
    assert "Hello, world!" in capsys.readouterr().out


def test_hello_with_name(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["hello", "--name", "Alice"])
    assert code == 0
    assert "Alice" in capsys.readouterr().out


def test_ping(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["ping"])
    assert code == 0
    assert capsys.readouterr().out.strip() == "pong"


def test_config_human(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PYTHON_FRAMEWORK_APP_NAME", "test-app")
    monkeypatch.setenv("PYTHON_FRAMEWORK_DEBUG", "true")
    code = main(["config"])
    assert code == 0
    out = capsys.readouterr().out
    assert "app_name=test-app" in out
    assert "debug=True" in out


def test_config_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PYTHON_FRAMEWORK_APP_NAME", "svc")
    monkeypatch.delenv("PYTHON_FRAMEWORK_DEBUG", raising=False)
    code = main(["config", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == {"app_name": "svc", "debug": False}


def test_version_exits_zero() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
