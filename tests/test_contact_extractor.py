from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIError, OpenAIError

from python_framework.models.contact_info import ContactInfo
from python_framework.services.contact_extractor import ContactExtractionError, ContactExtractor

EXPECTED = ContactInfo(
    name="Sarah Chen",
    email="sarah.chen@brightpath.io",
    phone="(415) 555-0198",
    company="BrightPath Analytics",
)

SAMPLE_BODY = """Hi there,

My name is Sarah Chen and I work at BrightPath Analytics.
You can reach me at sarah.chen@brightpath.io or call me at (415) 555-0198.

Best,
Sarah
"""


def _fake_completion(parsed: ContactInfo | None) -> SimpleNamespace:
    message = SimpleNamespace(parsed=parsed, refusal="model refused" if parsed is None else None)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def test_extract_returns_validated_model() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.parse.return_value = _fake_completion(EXPECTED)
    extractor = ContactExtractor(client=mock_client, model="gpt-test")

    result = extractor.extract_from_email(SAMPLE_BODY)

    assert isinstance(result, ContactInfo)
    assert result == EXPECTED
    mock_client.chat.completions.parse.assert_called_once()
    _, kwargs = mock_client.chat.completions.parse.call_args
    assert kwargs["model"] == "gpt-test"
    assert kwargs["response_format"] is ContactInfo


def test_json_serialization_and_exact_keys() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.parse.return_value = _fake_completion(EXPECTED)
    extractor = ContactExtractor(client=mock_client)

    result = extractor.extract_from_email(SAMPLE_BODY)
    data = result.model_dump()
    assert set(data.keys()) == {"name", "email", "phone", "company"}
    json_text = json.dumps(data, sort_keys=True)
    round_tripped = json.loads(json_text)
    assert round_tripped == {
        "name": "Sarah Chen",
        "email": "sarah.chen@brightpath.io",
        "phone": "(415) 555-0198",
        "company": "BrightPath Analytics",
    }


def test_empty_body_raises() -> None:
    mock_client = MagicMock()
    extractor = ContactExtractor(client=mock_client)

    with pytest.raises(ContactExtractionError, match="empty"):
        extractor.extract_from_email("  \n  ")

    mock_client.chat.completions.parse.assert_not_called()


def test_api_error_wrapped() -> None:
    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_client.chat.completions.parse.side_effect = APIError("upstream", request=req, body=None)
    extractor = ContactExtractor(client=mock_client)

    with pytest.raises(ContactExtractionError, match="OpenAI API error"):
        extractor.extract_from_email(SAMPLE_BODY)


def test_other_openai_error_wrapped() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.parse.side_effect = OpenAIError("client")
    extractor = ContactExtractor(client=mock_client)

    with pytest.raises(ContactExtractionError, match="OpenAI error"):
        extractor.extract_from_email(SAMPLE_BODY)


def test_missing_parsed_raises() -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.parse.return_value = _fake_completion(None)
    extractor = ContactExtractor(client=mock_client)

    with pytest.raises(ContactExtractionError, match="no structured output"):
        extractor.extract_from_email(SAMPLE_BODY)
