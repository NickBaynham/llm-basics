from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from pydantic import ValidationError

from python_framework.examples.structured_outputs_tutorial.client import (
    OpenAIRequestError,
    ask_openai,
)
from python_framework.examples.structured_outputs_tutorial.json_utils import parse_json
from python_framework.examples.structured_outputs_tutorial.models import (
    ExpenseReimbursement,
    VendorOnboardingRequest,
)
from python_framework.examples.structured_outputs_tutorial.pipelines import (
    extract_expense,
    route_expense_decision,
    run_incident_triage_pipeline,
    run_meeting_request_pipeline,
)
from python_framework.examples.structured_outputs_tutorial.responses_strict import (
    extract_vendor_onboarding_responses_api,
)
from python_framework.examples.structured_outputs_tutorial.validators import (
    validate_action_item,
    validate_meeting_request,
)
from python_framework.examples.structured_outputs_tutorial.verifiers import (
    verify_project_status_extraction,
)


def test_parse_json_strips_markdown_fence() -> None:
    raw = '```json\n{"x": 1}\n```'
    assert parse_json(raw) == {"x": 1}


_MEETING_OK = {
    "requester_name": "Emma Parker",
    "requester_email": "emma.parker@example.com",
    "contact_person": "Jordan Lee",
    "organization": "Northstar Labs",
    "meeting_topic": "infrastructure proposal",
    "proposed_time": "next Tuesday at 2 PM",
}


def test_validate_meeting_request_accepts_well_formed() -> None:
    m = validate_meeting_request(_MEETING_OK)
    assert m.requester_email == "emma.parker@example.com"


def test_validate_meeting_request_rejects_bad_email() -> None:
    bad = {**_MEETING_OK, "requester_email": "not-an-email"}
    with pytest.raises(ValueError, match="@"):
        validate_meeting_request(bad)


def test_validate_meeting_request_rejects_incomplete_dict() -> None:
    with pytest.raises(ValidationError):
        validate_meeting_request({"requester_name": "only this"})


_MEETING_SOURCE = (
    "Hi, can we meet next Tuesday at 2 PM with Jordan Lee from Northstar Labs "
    "to discuss the infrastructure proposal? My email is emma.parker@example.com."
)


def test_run_meeting_request_pipeline_exact_keys() -> None:
    client = MagicMock()
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        return_value=json.dumps(_MEETING_OK),
    ):
        ok, payload = run_meeting_request_pipeline(client, _MEETING_SOURCE)
    assert ok is True
    meeting = payload["meeting"]
    assert meeting is not None
    assert set(meeting) == {
        "requester_name",
        "requester_email",
        "contact_person",
        "organization",
        "meeting_topic",
        "proposed_time",
    }
    assert payload["verifier"]["is_acceptable"] is True


def test_verify_project_status_good_extraction_acceptable() -> None:
    source = """
    Project Atlas — data warehouse cutover
    Milestones: Schema freeze done 3/30. Load-test due 4/20.
    Risks: partner API rate limits.
    PM: Morgan Reeves; team ~8.
    """
    extracted = {
        "project_name": "Project Atlas",
        "milestones": [
            {"name": "Schema freeze", "status": "done", "due_date": "3/30"},
            {"name": "Load-test", "status": "planned", "due_date": "4/20"},
        ],
        "risks": ["partner API rate limits"],
        "team": {"manager": "Morgan Reeves", "contributors_count": 8},
    }
    verdict = verify_project_status_extraction(source, extracted)
    assert verdict.is_acceptable is True
    assert verdict.quality_score >= 80


def _httpx_resp(status: int = 400) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "https://api.openai.com/v1/"))


@pytest.mark.parametrize(
    ("side_effect", "match"),
    [
        (
            AuthenticationError("x", response=_httpx_resp(401), body=None),
            "API key",
        ),
        (
            RateLimitError("x", response=_httpx_resp(429), body=None),
            "Rate limited",
        ),
        (
            APIConnectionError(request=httpx.Request("GET", "https://api.openai.com/")),
            "Connection error",
        ),
        (
            BadRequestError("bad", response=_httpx_resp(400), body=None),
            "Bad request",
        ),
    ],
)
def test_ask_openai_maps_errors(side_effect: Exception, match: str) -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect
    with pytest.raises(OpenAIRequestError, match=match):
        ask_openai(client, system="s", user="u")


def test_ask_openai_empty_model_content() -> None:
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = None
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    with pytest.raises(OpenAIRequestError, match="empty"):
        ask_openai(client, system="s", user="u")


def test_validate_meeting_request_rejects_blank_topic() -> None:
    bad = {**_MEETING_OK, "meeting_topic": "   "}
    with pytest.raises(ValueError, match="meeting_topic"):
        validate_meeting_request(bad)


def test_validate_action_item_rejects_blank_owner() -> None:
    with pytest.raises(ValueError, match="owner"):
        validate_action_item(
            {"owner": "  ", "task": "x", "due_date": "1", "priority": "low"},
        )


def test_validate_action_item_accepts_dict() -> None:
    item = validate_action_item(
        {
            "owner": "Dana",
            "task": "finish checklist",
            "due_date": "Apr 12",
            "priority": "high",
        }
    )
    assert item.owner == "Dana"


def test_expense_category_validator_rejects_blank() -> None:
    with pytest.raises(ValidationError):
        ExpenseReimbursement.model_validate(
            {
                "category": "   ",
                "amount": 10.0,
                "urgency": "standard",
                "policy_risk": "low",
                "requires_manager_approval": False,
                "notes": "x",
            }
        )


def test_route_expense_fast_track_low_risk() -> None:
    exp = ExpenseReimbursement.model_validate(
        {
            "category": "travel",
            "amount": 100.0,
            "urgency": "same_day",
            "policy_risk": "low",
            "requires_manager_approval": False,
            "notes": "n",
        }
    )
    routed = route_expense_decision(exp, finance_threshold=500.0)
    assert "fast_track_payroll" in routed["actions"]


def test_route_expense_decision_threshold_and_risk() -> None:
    exp = ExpenseReimbursement.model_validate(
        {
            "category": "travel",
            "amount": 600.0,
            "urgency": "same_day",
            "policy_risk": "high",
            "requires_manager_approval": True,
            "notes": "n",
        }
    )
    routed = route_expense_decision(exp, finance_threshold=500.0)
    assert "route_to_finance_review" in routed["actions"]
    assert "flag_compliance" in routed["actions"]
    assert "fast_track_payroll" not in routed["actions"]


def test_extract_expense_uses_ask_openai() -> None:
    client = MagicMock()
    payload = {
        "category": "travel",
        "amount": 120.0,
        "urgency": "standard",
        "policy_risk": "low",
        "requires_manager_approval": False,
        "notes": "client dinner",
    }
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        return_value=json.dumps(payload),
    ):
        exp = extract_expense(client, "dinner with client")
    assert exp.amount == 120.0


def test_run_meeting_request_pipeline_openai_error() -> None:
    client = MagicMock()
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        side_effect=OpenAIRequestError("nope"),
    ):
        ok, payload = run_meeting_request_pipeline(client, "x")
    assert ok is False
    assert "nope" in payload["errors"][0]


def test_run_meeting_request_pipeline_bad_json() -> None:
    client = MagicMock()
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        return_value="not json",
    ):
        ok, payload = run_meeting_request_pipeline(client, "x")
    assert ok is False


def test_run_incident_triage_pipeline_openai_error() -> None:
    client = MagicMock()
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        side_effect=OpenAIRequestError("timeout"),
    ):
        ok, payload = run_incident_triage_pipeline(client, "ticket")
    assert ok is False
    assert "timeout" in payload["errors"][0]


def test_run_incident_triage_pipeline_invalid_json() -> None:
    client = MagicMock()
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        return_value="{",
    ):
        ok, payload = run_incident_triage_pipeline(client, "ticket")
    assert ok is False


def test_run_incident_triage_pipeline_success() -> None:
    client = MagicMock()
    triage_json = {
        "incident_type": "ci",
        "severity": "medium",
        "affected_system": "CI runners mobile queue",
        "needs_escalation": False,
        "summary_points": ["builds blocked"],
    }
    body = "CI runners for the mobile release queue are failing"
    with patch(
        "python_framework.examples.structured_outputs_tutorial.pipelines.ask_openai",
        return_value=json.dumps(triage_json),
    ):
        ok, payload = run_incident_triage_pipeline(client, body)
    assert ok is True
    assert payload["triage"]["incident_type"] == "ci"
    assert payload["verifier"]["quality_score"] >= 0


def test_verify_incident_triage_penalizes_missing_system_in_source() -> None:
    from python_framework.examples.structured_outputs_tutorial.verifiers import (
        verify_incident_triage_heuristic,
    )

    ticket = "VPN flaky for remote staff"
    extracted = {
        "incident_type": "net",
        "severity": "medium",
        "affected_system": "",
        "needs_escalation": False,
        "summary_points": ["x"],
    }
    v = verify_incident_triage_heuristic(ticket, extracted)
    assert v.quality_score < 80
    assert v.is_acceptable is False


def test_extract_vendor_responses_api_empty_output() -> None:
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text="")
    with pytest.raises(OpenAIRequestError, match="empty"):
        extract_vendor_onboarding_responses_api(client, "x", model="gpt-4o-mini")


def test_extract_vendor_responses_api_create_failure() -> None:
    client = MagicMock()
    client.responses.create.side_effect = RuntimeError("boom")
    with pytest.raises(OpenAIRequestError, match="Responses API"):
        extract_vendor_onboarding_responses_api(client, "x", model="gpt-4o-mini")


def test_extract_vendor_onboarding_responses_api_parses_pydantic() -> None:
    data = {
        "vendor_name": "Contoso Logistics",
        "service_type": "managed Kubernetes support",
        "contract_value": "USD 240k annually",
        "start_date": "May 1",
        "internal_owner": "Priya Nandakumar",
    }
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text=json.dumps(data))
    out = extract_vendor_onboarding_responses_api(client, "onboard contoso", model="gpt-4o-mini")
    assert isinstance(out, VendorOnboardingRequest)
    assert out.vendor_name == "Contoso Logistics"
    client.responses.create.assert_called_once()
    call_kw = client.responses.create.call_args.kwargs
    fmt = call_kw["text"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["strict"] is True
    assert fmt["schema"]["additionalProperties"] is False
