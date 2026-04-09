from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from python_framework.cli import build_parser, main
from python_framework.models.contact_info import ContactInfo


def test_build_parser_has_subcommands() -> None:
    parser = build_parser()
    # argparse stores the subparsers action on the _subparsers pseudo-action
    actions = {getattr(a, "dest", None): a for a in parser._actions}
    assert "command" in actions
    subaction = actions["command"]
    choices = getattr(subaction, "choices", None)
    assert choices is not None
    assert set(choices) >= {"hello", "ping", "config", "prompt-example", "run-examples"}


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


@pytest.fixture
def openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)


def test_prompt_example_prints_json(
    openai_api_key: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    expected = ContactInfo(
        name="Sarah Chen",
        email="sarah.chen@brightpath.io",
        phone="(415) 555-0198",
        company="BrightPath Analytics",
    )
    with patch("python_framework.examples.prompt_example.ContactExtractor") as ce_cls:
        ce_cls.return_value.extract_from_email.return_value = expected
        code = main(["--log-level", "CRITICAL", "prompt-example"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == expected.model_dump()
    assert set(data) == {"name", "email", "phone", "company"}


def test_run_examples_invokes_runner() -> None:
    with patch("python_framework.cli.run_all_examples_main", return_value=0) as runner:
        assert main(["run-examples"]) == 0
        runner.assert_called_once_with([])


def test_prompt_example_missing_api_key_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Block load_dotenv so a local .env does not restore OPENAI_API_KEY after delenv.
    monkeypatch.setattr("python_framework.cli.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "python_framework.examples.prompt_example.load_dotenv",
        lambda *args, **kwargs: None,
    )
    code = main(["prompt-example"])
    assert code == 1
    err = capsys.readouterr().err
    assert "OPENAI_API_KEY" in err


def test_prompt_example_passes_email_file(
    openai_api_key: None,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    expected = ContactInfo(
        name="Sarah Chen",
        email="sarah.chen@brightpath.io",
        phone="(415) 555-0198",
        company="BrightPath Analytics",
    )
    mail = tmp_path / "mail.txt"
    mail.write_text("email body", encoding="utf-8")
    with patch("python_framework.examples.prompt_example.ContactExtractor") as ce_cls:
        ce_cls.return_value.extract_from_email.return_value = expected
        code = main(["prompt-example", "--email-file", str(mail)])
    assert code == 0
    ce_cls.return_value.extract_from_email.assert_called_once_with("email body")
