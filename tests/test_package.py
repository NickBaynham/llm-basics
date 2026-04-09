from __future__ import annotations

import python_framework
from python_framework import __version__


def test_package_version_matches_pyproject() -> None:
    assert isinstance(__version__, str)
    assert __version__ == python_framework.__version__
