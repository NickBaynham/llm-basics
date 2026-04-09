"""Terminal runnable structured extraction example (contact fields from email text)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from python_framework.models.contact_info import ContactInfo
from python_framework.openai_settings import OpenAISettings
from python_framework.services.contact_extractor import ContactExtractionError, ContactExtractor

SAMPLE_EMAIL = """Hi there,

My name is Sarah Chen and I work at BrightPath Analytics.
You can reach me at sarah.chen@brightpath.io or call me at (415) 555-0198.

Best,
Sarah
"""


def _load_email_body(email_file: Path | None) -> str:
    if email_file is None:
        return SAMPLE_EMAIL
    return email_file.read_text(encoding="utf-8")


def run(*, email_file: Path | None = None) -> ContactInfo:
    """
    Load email text, call OpenAI structured extraction, return validated :class:`ContactInfo`.

    Raises:
        ContactExtractionError: extraction failures.
        ValidationError: settings cannot be loaded from the environment.
        OSError: email file cannot be read.
    """
    settings = OpenAISettings()
    body = _load_email_body(email_file)
    extractor = ContactExtractor(settings=settings)
    return extractor.extract_from_email(body)


def main(argv: list[str] | None = None) -> int:
    """Print extracted contact JSON to stdout or write errors to stderr."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract structured contact fields from email text using OpenAI.",
    )
    parser.add_argument(
        "--email-file",
        type=Path,
        default=None,
        help="Path to a UTF-8 text file containing the email body (default: built-in sample).",
    )
    args = parser.parse_args(argv)
    load_dotenv()

    try:
        contact = run(email_file=args.email_file)
    except ValidationError:
        print(
            "Configuration error: set OPENAI_API_KEY in the environment or a .env file "
            "(see .env.example).",
            file=sys.stderr,
        )
        return 1
    except ContactExtractionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Cannot read email file: {exc}", file=sys.stderr)
        return 1

    payload = contact.model_dump()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
