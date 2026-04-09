"""OpenAI-related settings from standard ``OPENAI_*`` environment variables."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    """API credentials and model name (load ``.env`` via :func:`dotenv.load_dotenv` before use)."""

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
        str_strip_whitespace=True,
    )

    api_key: str = Field(
        ...,
        validation_alias="OPENAI_API_KEY",
        description="OpenAI API key (required).",
    )
    model: str = Field(
        default="gpt-4.1-mini",
        validation_alias="OPENAI_MODEL",
        description="Chat model id for completions.",
    )

    @field_validator("api_key")
    @classmethod
    def api_key_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "OPENAI_API_KEY is missing or empty"
            raise ValueError(msg)
        return v.strip()
