"""Runtime configuration from environment variables (Pydantic Settings)."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings from ``PYTHON_FRAMEWORK_*`` env vars (call ``load_dotenv()`` for ``.env``)."""

    model_config = SettingsConfigDict(
        env_prefix="PYTHON_FRAMEWORK_",
        extra="ignore",
        str_strip_whitespace=True,
    )

    app_name: str = "python-framework"
    debug: bool = False

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: object) -> bool:
        if isinstance(v, bool):
            return v
        if v is None or v == "":
            return False
        s = str(v).strip().lower()
        return s in {"1", "true", "yes", "on"}
