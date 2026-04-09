"""Helpers for recovering JSON from model text (fences, prose)."""

from __future__ import annotations

import json
import re
from typing import Any


def parse_json(text: str) -> Any:
    """
    Strip optional Markdown code fences and parse JSON.

    - Trims whitespace.
    - If the payload is wrapped in `` ```json ... ``` `` (or plain `` ``` ``),
      extracts the inner block.
    - Parses with :func:`json.loads`.

    Raises:
        json.JSONDecodeError: if no valid JSON object/array is found.
    """
    raw = text.strip()
    fence = re.search(
        r"^```(?:json)?\s*\n(?P<body>.*?)\n```\s*$",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fence:
        raw = fence.group("body").strip()
    return json.loads(raw)
