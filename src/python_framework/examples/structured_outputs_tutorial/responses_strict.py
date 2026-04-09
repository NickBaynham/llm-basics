"""Strict JSON Schema via the Responses API (vendor onboarding)."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from python_framework.examples.structured_outputs_tutorial.client import (
    OpenAIRequestError,
    resolve_model,
)
from python_framework.examples.structured_outputs_tutorial.models import VendorOnboardingRequest

# Explicit JSON Schema aligned with :class:`VendorOnboardingRequest` (strict, no extra keys).
_VENDOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "vendor_name": {"type": "string"},
        "service_type": {"type": "string"},
        "contract_value": {"type": "string"},
        "start_date": {"type": "string"},
        "internal_owner": {"type": "string"},
    },
    "required": [
        "vendor_name",
        "service_type",
        "contract_value",
        "start_date",
        "internal_owner",
    ],
    "additionalProperties": False,
}


def extract_vendor_onboarding_responses_api(
    client: OpenAI,
    raw_text: str,
    *,
    model: str | None = None,
) -> VendorOnboardingRequest:
    """
    Use ``client.responses.create`` with ``text.format`` = json_schema + ``strict: True``.

    Parsed output is validated again with Pydantic for local type safety.
    """
    mid = resolve_model(model)
    prompt = (
        "Extract vendor onboarding details from the message as JSON matching the schema. "
        "Be precise; use strings for contract_value and start_date as written.\n\n"
        f"Message:\n{raw_text}"
    )
    try:
        resp = client.responses.create(
            model=mid,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "vendor_onboarding_request",
                    "strict": True,
                    "schema": _VENDOR_SCHEMA,
                }
            },
        )
    except Exception as exc:
        raise OpenAIRequestError(f"Responses API error: {exc}") from exc

    blob = resp.output_text
    if not blob:
        raise OpenAIRequestError("Responses API returned empty output_text.")
    data = json.loads(blob)
    return VendorOnboardingRequest.model_validate(data)
