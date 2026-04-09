"""Runtime configuration sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Framework settings with explicit, minimal surface area."""

    app_name: str
    debug: bool

    @classmethod
    def from_environ(cls, environ: dict[str, str] | None = None) -> Settings:
        """Build settings from a mapping (defaults to ``os.environ``)."""
        env = os.environ if environ is None else environ
        raw_debug = env.get("PYTHON_FRAMEWORK_DEBUG", "").lower()
        debug = raw_debug in {"1", "true", "yes", "on"}
        return cls(
            app_name=env.get("PYTHON_FRAMEWORK_APP_NAME", "python-framework"),
            debug=debug,
        )
