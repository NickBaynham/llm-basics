from __future__ import annotations

from unittest.mock import patch

from python_framework.examples.run_all import main as run_all_main


def test_run_all_runs_each_registered_example() -> None:
    with patch("python_framework.examples.prompt_example.main", return_value=0) as pe_main:
        assert run_all_main() == 0
        pe_main.assert_called_once_with([])


def test_run_all_returns_first_nonzero_exit() -> None:
    with patch("python_framework.examples.prompt_example.main", return_value=3) as pe_main:
        assert run_all_main() == 3
        pe_main.assert_called_once_with([])
