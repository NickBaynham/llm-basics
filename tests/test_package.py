from __future__ import annotations

import re

import python_framework
from python_framework import __version__


def test_package_version_is_pep440_like() -> None:
    assert isinstance(__version__, str)
    assert __version__ == python_framework.__version__
    msg = "expect PEP 440-style metadata from install/build"
    assert re.match(r"^\d+\.\d+(\.\d+)?", __version__), msg
