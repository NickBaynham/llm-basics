"""OpenAI client setup and a small ``ask_openai`` helper with production-style error mapping."""

from __future__ import annotations

import logging

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from pydantic import ValidationError

from python_framework.openai_settings import OpenAISettings

log = logging.getLogger(__name__)

# Default for tutorial calls; override with OPENAI_MODEL in .env
DEFAULT_MODEL = "gpt-4.1-mini"


class OpenAIRequestError(RuntimeError):
    """Raised when ``ask_openai`` fails after a mapped API or transport error."""


def make_client(settings: OpenAISettings | None = None) -> OpenAI:
    """Build a synchronous :class:`openai.OpenAI` client from settings (env / ``.env``)."""
    cfg = settings or OpenAISettings()
    return OpenAI(api_key=cfg.api_key)


def resolve_model(explicit: str | None, settings: OpenAISettings | None = None) -> str:
    """
    Return ``explicit`` if set, else ``OPENAI_MODEL`` from settings, else :data:`DEFAULT_MODEL`.
    """
    if explicit and explicit.strip():
        return explicit.strip()
    try:
        cfg = settings or OpenAISettings()
        return cfg.model
    except ValidationError:
        return DEFAULT_MODEL


def ask_openai(
    client: OpenAI,
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
    settings: OpenAISettings | None = None,
) -> str:
    """
    One chat completion; returns assistant **text** (may be JSON-shaped).

    Maps common failures to :exc:`OpenAIRequestError` with a short, actionable message.
    """
    mid = resolve_model(model, settings=settings)
    log.debug("ask_openai", extra={"model": mid, "user_chars": len(user)})
    try:
        completion = client.chat.completions.create(
            model=mid,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except AuthenticationError as exc:
        raise OpenAIRequestError("Invalid or missing API key (check OPENAI_API_KEY).") from exc
    except RateLimitError as exc:
        raise OpenAIRequestError("Rate limited by OpenAI; retry with backoff.") from exc
    except APIConnectionError as exc:
        raise OpenAIRequestError("Connection error talking to OpenAI.") from exc
    except APITimeoutError as exc:
        raise OpenAIRequestError("OpenAI request timed out.") from exc
    except BadRequestError as exc:
        raise OpenAIRequestError(f"Bad request to OpenAI: {exc}") from exc
    except APIError as exc:
        raise OpenAIRequestError(f"OpenAI API error: {exc}") from exc
    except OpenAIError as exc:
        raise OpenAIRequestError(f"OpenAI client error: {exc}") from exc

    choice = completion.choices[0]
    content = choice.message.content
    if content is None:
        raise OpenAIRequestError("Model returned empty content.")
    return content.strip()
