"""Guardrails so the production image stays non-interactive, venv-free, and pip-based."""

from __future__ import annotations

from pathlib import Path


def _dockerfile_text() -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / "Dockerfile").read_text(encoding="utf-8")


def test_dockerfile_uses_export_and_system_prefix_not_venv() -> None:
    text = _dockerfile_text()
    assert "pdm export --prod" in text
    assert "pip install" in text
    assert "/usr/local/lib/${PYTHON_LIBDIR}/site-packages" in text
    assert "python -m venv" not in text
    assert ".venv" not in text


def test_dockerfile_pins_python_libdir_with_runtime() -> None:
    text = _dockerfile_text()
    assert "ARG PYTHON_LIBDIR" in text
    assert "ARG PYTHON_VERSION" in text
