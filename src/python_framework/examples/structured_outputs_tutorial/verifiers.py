"""Quality checks that compare source text to extracted JSON (verifier pattern)."""

from __future__ import annotations

from typing import Any

from python_framework.examples.structured_outputs_tutorial.models import VerifierResult

_ACCEPT_THRESHOLD = 80


def verify_meeting_request_heuristic(source_text: str, meeting: dict[str, Any]) -> VerifierResult:
    """Cheap checks: named people/org and email should echo the source message."""
    issues: list[str] = []
    score = 100
    norm = source_text.lower()
    for key in ("contact_person", "organization", "requester_email"):
        val = meeting.get(key, "")
        if not isinstance(val, str) or not val.strip():
            issues.append(f"{key} empty")
            score -= 25
            continue
        if val.lower() not in norm:
            issues.append(f"{key} not found verbatim in source")
            score -= 20
    score = max(0, min(100, score))
    return VerifierResult(
        quality_score=score, issues=issues, is_acceptable=score >= _ACCEPT_THRESHOLD
    )


def verify_project_status_extraction(source_text: str, extracted: dict[str, Any]) -> VerifierResult:
    """
    Lightweight verifier: overlap between source and key fields (no second LLM call).

    Use this in tutorials and tests; production teams often add a model-based judge
    or rules engine on top once volume and risk justify it.

    Scoring (illustrative):
    - project_name substring in source
    - each milestone name weakly mentioned
    - at least one risk string appears in source
    - manager name appears
    """
    issues: list[str] = []
    score = 0
    norm = source_text.lower()

    name = extracted.get("project_name", "")
    if isinstance(name, str) and name and name.lower() in norm:
        score += 30
    else:
        issues.append("project_name missing or not found in source text")

    milestones = extracted.get("milestones") or []
    if isinstance(milestones, list) and milestones:
        hits = 0
        for m in milestones:
            if not isinstance(m, dict):
                continue
            mn = m.get("name", "")
            if isinstance(mn, str) and mn and mn.lower() in norm:
                hits += 1
        ratio = hits / max(len(milestones), 1)
        score += int(40 * ratio)
        if ratio < 1.0:
            issues.append("some milestone names were not anchored in the source")
    else:
        issues.append("milestones empty or not a list")

    risks = extracted.get("risks") or []
    if isinstance(risks, list) and risks:
        found = sum(1 for r in risks if isinstance(r, str) and r and r.lower() in norm)
        if found > 0:
            score += 20
        else:
            issues.append("risk strings do not appear verbatim in source (possible hallucination)")
    else:
        issues.append("risks missing")

    team = extracted.get("team") or {}
    mgr = team.get("manager", "") if isinstance(team, dict) else ""
    if isinstance(mgr, str) and mgr and mgr.lower() in norm:
        score += 10
    else:
        issues.append("team.manager not found in source")

    score = min(100, score)
    acceptable = score >= _ACCEPT_THRESHOLD
    return VerifierResult(quality_score=score, issues=issues, is_acceptable=acceptable)


def verify_incident_triage_heuristic(source_text: str, extracted: dict[str, Any]) -> VerifierResult:
    """Small verifier for triage: severity word and system name should echo the ticket."""
    issues: list[str] = []
    score = 100
    norm = source_text.lower()

    system = extracted.get("affected_system", "")
    if not (isinstance(system, str) and system.strip()):
        issues.append("affected_system empty")
        score -= 35
    elif system.lower() not in norm:
        issues.append("affected_system not literally present in ticket text")
        score -= 20

    sev = extracted.get("severity", "")
    if sev in {"critical", "high"}:
        if isinstance(sev, str) and sev in norm:
            pass
        else:
            issues.append("high/critical severity not clearly grounded in wording")
            score -= 15

    score = max(0, min(100, score))
    return VerifierResult(
        quality_score=score, issues=issues, is_acceptable=score >= _ACCEPT_THRESHOLD
    )
