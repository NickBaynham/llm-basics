"""Explicit validation helpers (beyond Pydantic ``model_validate``)."""

from __future__ import annotations

from typing import Any

from python_framework.examples.structured_outputs_tutorial.models import (
    ActionItem,
    MeetingRequest,
)


def validate_meeting_request(data: dict[str, Any] | MeetingRequest) -> MeetingRequest:
    """
    Ensure meeting-request extraction is usable: types, non-empty critical fields, email shape.

    Raises:
        ValidationError: Pydantic validation failed.
        ValueError: business rules (e.g. email must contain ``@``).
    """
    obj = MeetingRequest.model_validate(data)
    if "@" not in obj.requester_email:
        raise ValueError("requester_email must look like an email (contain '@').")
    for name, val in (
        ("requester_name", obj.requester_name),
        ("contact_person", obj.contact_person),
        ("organization", obj.organization),
        ("meeting_topic", obj.meeting_topic),
    ):
        if not val.strip():
            raise ValueError(f"{name} must not be empty")
    return obj


def validate_action_item(item: dict[str, Any] | ActionItem) -> ActionItem:
    """
    Validate a single action item: types, non-empty strings, allowed priority.

    Raises:
        ValidationError: invalid types / missing fields.
        ValueError: empty task/owner or unknown priority string.
    """
    obj = ActionItem.model_validate(item)
    if not obj.owner.strip() or not obj.task.strip() or not obj.due_date.strip():
        raise ValueError("owner, task, and due_date must be non-empty strings.")
    return obj
