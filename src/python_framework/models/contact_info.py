"""Structured contact fields extracted from email text."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact details produced by the LLM and validated before use."""

    name: str = Field(description="Full name of the sender.")
    email: str = Field(description="Email address.")
    phone: str = Field(description="Phone number as written in the message.")
    company: str = Field(description="Company or organization name.")
