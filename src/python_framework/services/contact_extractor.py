"""Extract structured contact fields from plain-text email bodies via OpenAI."""

from __future__ import annotations

import logging

from openai import APIError, OpenAI, OpenAIError

from python_framework.models.contact_info import ContactInfo
from python_framework.openai_settings import OpenAISettings

log = logging.getLogger(__name__)


class ContactExtractionError(RuntimeError):
    """Raised when extraction fails after a request or validation error."""


_DEFAULT_SYSTEM = (
    "You extract contact information from informal email text. "
    "Return only the fields in the structured schema: full name, primary email, "
    "phone exactly as written, and company name. If a field is not present, use an empty string."
)


class ContactExtractor:
    """
    Calls OpenAI chat completions with a Pydantic response schema.

    Pass a pre-configured :class:`openai.OpenAI` client in tests; otherwise the client
    is built from :class:`~python_framework.openai_settings.OpenAISettings`.
    """

    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        model: str | None = None,
        settings: OpenAISettings | None = None,
        system_prompt: str = _DEFAULT_SYSTEM,
    ) -> None:
        self._system_prompt = system_prompt
        if client is not None:
            self._client = client
            cfg = settings
            self._model = model or (cfg.model if cfg is not None else "gpt-4.1-mini")
            return
        cfg = settings or OpenAISettings()
        self._client = OpenAI(api_key=cfg.api_key)
        self._model = model or cfg.model

    def extract_from_email(self, email_body: str) -> ContactInfo:
        """
        Send ``email_body`` to the model and return a validated :class:`ContactInfo`.

        Raises:
            ContactExtractionError: missing configuration, API failure, or empty / invalid parse.
        """
        text = email_body.strip()
        if not text:
            raise ContactExtractionError("Email body is empty")

        log.debug("contact extract request", extra={"model": self._model, "chars": len(text)})
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format=ContactInfo,
            )
        except APIError as exc:
            log.warning("OpenAI API error", exc_info=True)
            raise ContactExtractionError(f"OpenAI API error: {exc}") from exc
        except OpenAIError as exc:
            log.warning("OpenAI client error", exc_info=True)
            raise ContactExtractionError(f"OpenAI error: {exc}") from exc

        message = completion.choices[0].message
        parsed = message.parsed
        if parsed is None:
            raise ContactExtractionError(
                "Model returned no structured output; refuse_reason="
                f"{getattr(message, 'refusal', None)!r}"
            )
        return parsed
