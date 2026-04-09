from __future__ import annotations

import json

import pytest

from python_framework.cli import build_parser, main


def test_build_parser_has_subcommands() -> None:
    parser = build_parser()
    # argparse stores the subparsers action on the _subparsers pseudo-action
    actions = {getattr(a, "dest", None): a for a in parser._actions}
    assert "command" in actions
    subaction = actions["command"]
    choices = getattr(subaction, "choices", None)
    assert choices is not None
    assert set(choices) >= {"hello", "ping", "config"}


def test_build_parser_has_logging_flags() -> None:
    parser = build_parser()
    flags = {a.dest for a in parser._actions if hasattr(a, "dest")}
    assert "log_level" in flags
    assert "log_json" in flags


def test_hello_default(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--log-level", "CRITICAL", "hello"])
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


def test_main_log_json_writes_structured_log(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--log-level", "INFO", "--log-json", "ping"])
    assert code == 0
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert any('"level": "INFO"' in ln and "ping" in ln for ln in lines)
