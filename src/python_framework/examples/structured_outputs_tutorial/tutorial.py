"""
Progressive structured-output tutorial (operations / admin scenarios).

Sections map to the learning goals: fragile text → JSON → parsing → nested data →
validation → verifiers → pipelines → Responses API strict schema → business logic → exercise.
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from python_framework.examples.structured_outputs_tutorial.client import (
    OpenAIRequestError,
    ask_openai,
    make_client,
)
from python_framework.examples.structured_outputs_tutorial.exercise import (
    SoftwareAccessRequestExercise,
)
from python_framework.examples.structured_outputs_tutorial.json_utils import parse_json
from python_framework.examples.structured_outputs_tutorial.models import (
    IncidentTriage,
    MeetingActionItems,
    ProjectStatus,
)
from python_framework.examples.structured_outputs_tutorial.pipelines import (
    extract_expense,
    route_expense_decision,
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


def _print(title: str) -> None:
    bar = "=" * min(len(title) + 8, 72)
    print(f"\n{bar}\n  {title}\n{bar}\n")


def section_01_ticket_priority_few_shot(client: OpenAI) -> None:
    _print("1. Few-shot labels (fragile for automation)")
    system = (
        "You are an internal support router. Classify priority as exactly one word: "
        "low, medium, or high. No JSON."
    )
    user = """Examples:
Message: "Printer works" -> low
Message: "VPN drops weekly" -> medium
Message: "Payroll batch stuck since 6am, 400 people unpaid" -> high
Message: "Our SSO IdP cert expired; nobody can log in to HR tools" ->"""
    text = ask_openai(client, system=system, user=user)
    print("Model output (free text):\n", text)
    print(
        "\nWhy this is fragile in production: downstream code cannot rely on "
        "consistent casing, spelling, or extra words without extra parsing."
    )


_MEETING_MSG = (
    "Hi, can we meet next Tuesday at 2 PM with Jordan Lee from Northstar Labs "
    "to discuss the infrastructure proposal? My email is emma.parker@example.com."
)


def section_02_meeting_json(client: OpenAI) -> None:
    _print("2. First structured extraction — meeting request")
    system = (
        "Extract fields from the user message. Reply with ONLY valid JSON (no markdown) "
        "with keys: requester_name, requester_email, contact_person, organization, "
        "meeting_topic, proposed_time."
    )
    user = f"Message:\n{_MEETING_MSG}"
    raw = ask_openai(client, system=system, user=user)
    print("Raw model output:\n", raw)
    data = parse_json(raw)
    print("\nParsed Python dict:\n", json.dumps(data, indent=2))
    meeting = validate_meeting_request(data)
    print("\nValidated Pydantic model:\n", meeting.model_dump_json(indent=2))


def section_03_parse_json_utility() -> None:
    _print("3. parse_json(text) utility")
    sample = '```json\n{"a": 1}\n```'
    print("Input:", repr(sample))
    print("Output:", parse_json(sample))


_FEW_SHOT_TRIAGE = """
Examples:
Input: "VPN for the Dublin office keeps dropping" ->
{"incident_type":"network","severity":"medium","affected_system":"VPN Dublin",
"needs_escalation":false,"summary_points":["VPN instability","office-specific"]}
Input: "Prod Postgres replication lag 45min, finance ledger at risk" ->
{"incident_type":"database","severity":"critical","affected_system":"Postgres prod",
"needs_escalation":true,"summary_points":["replication lag","finance impact"]}
Now triage:
Input: "CI runners for the mobile release queue are failing — builds blocked for 2 teams" ->
""".strip()


def section_04_incident_few_shot_json(client: OpenAI) -> None:
    _print("4. Few-shot + explicit JSON — IT incident triage")
    system = (
        "You return ONLY JSON for IT incident triage with keys incident_type, severity, "
        "affected_system, needs_escalation, summary_points. Follow the few-shot style exactly."
    )
    raw = ask_openai(client, system=system, user=_FEW_SHOT_TRIAGE)
    triage = IncidentTriage.model_validate(parse_json(raw))
    print(triage.model_dump_json(indent=2))


_MEETING_NOTES = """
Ops weekly — Apr 7
- Dana: finish vendor DPIA checklist by Apr 12 (high)
- Luis: ship backup restore drill doc to SecOps — due Apr 10 (medium)
- Avery: open ticket for budget overrun on Atlas migration — due Apr 15 (high)
"""


def section_05_action_items(client: OpenAI) -> None:
    _print("5. Multiple records — action items from meeting notes")
    system = (
        "Extract action items from notes. Reply ONLY JSON: "
        '{ "items": [ {"owner","task","due_date","priority"} ... ] } '
        "priority is low|medium|high."
    )
    raw = ask_openai(client, system=system, user=_MEETING_NOTES)
    bundle = MeetingActionItems.model_validate(parse_json(raw))
    for i, item in enumerate(bundle.items, start=1):
        v = validate_action_item(item)
        print(i, v.model_dump())


_PROJECT_BLURB = """
Project Atlas — data warehouse cutover
Budget: originally $1.1M; spend tracking $1.18M (slightly over).
Milestones: (1) Schema freeze — done 3/30. (2) Load-test — in progress, due 4/20.
(3) Go-live rehearsal — scheduled 4/28.
Risks: partner API rate limits; legacy ODBC driver EOL in May.
Timeline health is yellow — next hard deadline is load-test signoff on 4/20.
PM: Morgan Reeves; team size ~8 ICs on the core workstream.
"""


def section_06_project_nested(client: OpenAI) -> None:
    _print("6. Nested schema — project status")
    system = (
        "Extract a project status JSON object with: project_name; "
        "budget: {status, variance_percent}; "
        "milestones: [{name, status, due_date}]; risks: string[]; "
        "timeline: {health, next_deadline}; team: {manager, contributors_count}. "
        "budget.status: on_track|at_risk|over_budget|unknown. "
        "timeline.health: green|yellow|red|unknown. ONLY JSON, no fences."
    )
    raw = ask_openai(client, system=system, user=_PROJECT_BLURB)
    report = ProjectStatus.model_validate(parse_json(raw))
    print("Nested access:", report.budget.status, report.milestones[0].name)


def section_07_validation() -> None:
    _print("7. Validation — meeting request + action item")
    good = {
        "requester_name": "Emma Parker",
        "requester_email": "emma.parker@example.com",
        "contact_person": "Jordan Lee",
        "organization": "Northstar Labs",
        "meeting_topic": "infrastructure proposal",
        "proposed_time": "next Tuesday at 2 PM",
    }
    print("valid:", validate_meeting_request(good))
    try:
        bad = {**good, "requester_email": "not-an-email"}
        validate_meeting_request(bad)
    except Exception as exc:
        print("expected failure (email):", type(exc).__name__, exc)
    try:
        validate_action_item({"owner": "", "task": "x", "due_date": "Friday", "priority": "low"})
    except Exception as exc:
        print("expected failure (action item):", type(exc).__name__, exc)


def section_08_verifier() -> None:
    _print("8. Verifier pattern — project status")
    source = _PROJECT_BLURB
    good = {
        "project_name": "Project Atlas",
        "milestones": [
            {"name": "Schema freeze", "status": "done", "due_date": "3/30"},
            {"name": "Load-test", "status": "in progress", "due_date": "4/20"},
        ],
        "risks": ["partner API rate limits", "legacy ODBC driver EOL in May"],
        "team": {"manager": "Morgan Reeves", "contributors_count": 8},
    }
    weak = {
        "project_name": "Unknown codename",
        "milestones": [],
        "risks": [],
        "team": {"manager": "nobody", "contributors_count": 0},
    }
    print("good:", verify_project_status_extraction(source, good).model_dump())
    print("weak:", verify_project_status_extraction(source, weak).model_dump())
    print(
        "\nWhen to use verifiers: high-stakes fields, regulatory hooks, or when a second "
        "model/human review is cheaper than downstream incidents."
    )


def section_09_pipeline(client: OpenAI) -> None:
    _print("9. Full pipeline — meeting request")
    ok, payload = run_meeting_request_pipeline(client, _MEETING_MSG)
    print("success:", ok)
    print(json.dumps(payload, indent=2))


def section_10_responses_strict(client: OpenAI) -> None:
    _print("10. Strict schema — Responses API (vendor onboarding)")
    note = (
        "Please onboard Contoso Logistics for managed Kubernetes support. "
        "Contract value USD 240k annually, start May 1. "
        "Engagement owner on our side: Priya Nandakumar."
    )
    vendor = extract_vendor_onboarding_responses_api(client, note)
    print(vendor.model_dump_json(indent=2))


def section_11_expense_logic(client: OpenAI) -> None:
    _print("11. Business logic on structured fields — reimbursement")
    text = (
        "I need same-day reimbursement for $780 flight change fee to fix a customer outage visit. "
        "Policy looks medium risk because justification is thin in Concur."
    )
    exp = extract_expense(client, text)
    decision = route_expense_decision(exp, finance_threshold=500.0)
    print(json.dumps(decision, indent=2))


def section_12_exercise() -> None:
    _print("12. Exercise — finish SoftwareAccessRequestExercise")
    print(SoftwareAccessRequestExercise.__doc__ or "")
    print("Model fields today:", SoftwareAccessRequestExercise.model_fields.keys())


def run_tutorial(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structured outputs tutorial (live OpenAI calls).")
    parser.add_argument(
        "--only",
        type=str,
        default="all",
        help='Comma-separated section numbers 1-12, or "all" (default: all).',
    )
    args = parser.parse_args(argv)
    load_dotenv()
    try:
        client = make_client()
    except ValidationError as exc:
        print(f"Cannot load OpenAI settings: {exc}", file=sys.stderr)
        return 1

    if args.only.strip().lower() == "all":
        wanted = set(range(1, 13))
    else:
        wanted = {int(x.strip()) for x in args.only.split(",") if x.strip()}

    steps = {
        1: lambda: section_01_ticket_priority_few_shot(client),
        2: lambda: section_02_meeting_json(client),
        3: section_03_parse_json_utility,
        4: lambda: section_04_incident_few_shot_json(client),
        5: lambda: section_05_action_items(client),
        6: lambda: section_06_project_nested(client),
        7: section_07_validation,
        8: section_08_verifier,
        9: lambda: section_09_pipeline(client),
        10: lambda: section_10_responses_strict(client),
        11: lambda: section_11_expense_logic(client),
        12: section_12_exercise,
    }
    try:
        for n in sorted(wanted):
            if n not in steps:
                print(f"Unknown section {n}", file=sys.stderr)
                return 1
            steps[n]()
    except OpenAIRequestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    return run_tutorial(argv)


if __name__ == "__main__":
    raise SystemExit(main())
