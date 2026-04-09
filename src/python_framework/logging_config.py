"""Application logging: Rich console or JSON lines for containers and aggregators."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any


def _want_rich() -> bool:
    if os.environ.get("PYTHON_FRAMEWORK_PLAIN_LOG", "").lower() in {"1", "true", "yes", "on"}:
        return False
    # Rich can block or mis-detect terminals in Docker/non-interactive runs; use plain logs there.
    return sys.stderr.isatty()


class _JsonLineFormatter(logging.Formatter):
    """Minimal structured formatter (one JSON object per line)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str | int = "WARNING", *, json_format: bool = False) -> None:
    """Attach handlers to the ``python_framework`` logger tree (idempotent per process)."""
    pkg = logging.getLogger("python_framework")
    pkg.handlers.clear()
    pkg.setLevel(logging.DEBUG)

    handler: logging.Handler
    if json_format:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonLineFormatter())
    elif _want_rich():
        from rich.logging import RichHandler

        handler = RichHandler(
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s %(message)s"),
        )

    numeric = level if isinstance(level, int) else getattr(logging, level.upper(), logging.WARNING)
    handler.setLevel(numeric)
    pkg.addHandler(handler)
    pkg.propagate = False
