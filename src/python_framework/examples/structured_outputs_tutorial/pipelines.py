"""End-to-end flows: extract → parse → validate → verify."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from python_framework.examples.structured_outputs_tutorial.client import (
    OpenAIRequestError,
    ask_openai,
)
from python_framework.examples.structured_outputs_tutorial.json_utils import parse_json
from python_framework.examples.structured_outputs_tutorial.models import (
    ExpenseReimbursement,
    IncidentTriage,
)
from python_framework.examples.structured_outputs_tutorial.validators import (
    validate_meeting_request,
)
from python_framework.examples.structured_outputs_tutorial.verifiers import (
    verify_incident_triage_heuristic,
    verify_meeting_request_heuristic,
)

_MEETING_SYS = (
    "You extract structured meeting requests. Reply with ONLY valid JSON, no markdown fence. "
    "Keys: requester_name, requester_email, contact_person, organization, meeting_topic, "
    "proposed_time."
)

_TRIAGE_SYS = """You triage internal IT incidents. Reply with ONLY JSON (no fences) with keys:
incident_type, severity (low|medium|high|critical), affected_system, needs_escalation (boolean),
summary_points (array of short strings)."""


def run_meeting_request_pipeline(
    client: OpenAI,
    raw_message: str,
    *,
    model: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Parse JSON, run :func:`validate_meeting_request`, then
    :func:`verify_meeting_request_heuristic`.

    Returns:
        On success: ``(True, {"meeting": {...}, "verifier": {...}, "errors": []})``.
        On failure: ``(False, {..., "errors": [...]})``.
    """
    out: dict[str, Any] = {"meeting": None, "verifier": None, "errors": []}
    try:
        text = ask_openai(
            client,
            system=_MEETING_SYS,
            user=raw_message,
            model=model,
        )
        data = parse_json(text)
        meeting = validate_meeting_request(data)
        dump = meeting.model_dump()
        verdict = verify_meeting_request_heuristic(raw_message, dump)
        out["meeting"] = dump
        out["verifier"] = verdict.model_dump()
        ok = verdict.is_acceptable
        return ok, out
    except OpenAIRequestError as exc:
        out["errors"].append(str(exc))
        return False, out
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        out["errors"].append(f"{type(exc).__name__}: {exc}")
        return False, out


def run_incident_triage_pipeline(
    client: OpenAI,
    ticket_body: str,
    *,
    model: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Full triage path: LLM JSON → Pydantic → heuristic verifier.

    Returns payload with ``triage``, ``verifier``, and ``errors``.
    """
    payload: dict[str, Any] = {"triage": None, "verifier": None, "errors": []}
    try:
        text = ask_openai(client, system=_TRIAGE_SYS, user=ticket_body, model=model)
        triage = IncidentTriage.model_validate(parse_json(text))
        verdict = verify_incident_triage_heuristic(ticket_body, triage.model_dump())
        payload["triage"] = triage.model_dump()
        payload["verifier"] = verdict.model_dump()
        ok = verdict.is_acceptable
        return ok, payload
    except OpenAIRequestError as exc:
        payload["errors"].append(str(exc))
        return False, payload
    except (json.JSONDecodeError, ValidationError) as exc:
        payload["errors"].append(f"{type(exc).__name__}: {exc}")
        return False, payload


_EXPENSE_SYS = """You classify internal expense reimbursement requests for routing.
Return ONLY JSON with keys: category, amount (number), urgency (standard|same_week|same_day),
policy_risk (low|medium|high), requires_manager_approval (boolean), notes (string)."""


def extract_expense(
    client: OpenAI, description: str, *, model: str | None = None
) -> ExpenseReimbursement:
    """LLM extraction for :class:`ExpenseReimbursement`."""
    text = ask_openai(client, system=_EXPENSE_SYS, user=description, model=model)
    return ExpenseReimbursement.model_validate(parse_json(text))


def route_expense_decision(
    expense: ExpenseReimbursement,
    *,
    finance_threshold: float = 500.0,
) -> dict[str, Any]:
    """
    Example business rules on structured fields (why schemas matter in production).

    - Amount over ``finance_threshold`` → finance review queue.
    - High policy risk → compliance flag.
    - Urgent + low policy risk → fast-track marker.
    """
    actions: list[str] = []
    if expense.amount > finance_threshold:
        actions.append("route_to_finance_review")
    if expense.policy_risk == "high":
        actions.append("flag_compliance")
    if expense.urgency == "same_day" and expense.policy_risk == "low":
        actions.append("fast_track_payroll")

    return {
        "expense": expense.model_dump(),
        "actions": actions,
        "requires_manager": expense.requires_manager_approval,
    }
