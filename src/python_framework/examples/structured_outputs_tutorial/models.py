"""Typed shapes for structured extraction examples."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeetingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requester_name: str
    requester_email: str
    contact_person: str
    organization: str
    meeting_topic: str
    proposed_time: str


class IncidentTriage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_type: str
    severity: Literal["low", "medium", "high", "critical"]
    affected_system: str
    needs_escalation: bool
    summary_points: list[str]


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str
    task: str
    due_date: str
    priority: Literal["low", "medium", "high"]


class MeetingActionItems(BaseModel):
    """Wrapper so JSON has a clear root key for a list of items."""

    model_config = ConfigDict(extra="forbid")

    items: list[ActionItem]


class Milestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: str
    due_date: str


class BudgetBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["on_track", "at_risk", "over_budget", "unknown"]
    variance_percent: float | None = None


class TimelineBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health: Literal["green", "yellow", "red", "unknown"]
    next_deadline: str


class TeamBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manager: str
    contributors_count: int = Field(ge=0)


class ProjectStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str
    budget: BudgetBlock
    milestones: list[Milestone]
    risks: list[str]
    timeline: TimelineBlock
    team: TeamBlock


class VendorOnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    service_type: str
    contract_value: str
    start_date: str
    internal_owner: str


class ExpenseReimbursement(BaseModel):
    """Fields for internal reimbursement triage."""

    model_config = ConfigDict(extra="forbid")

    category: str
    amount: float = Field(ge=0)
    urgency: Literal["standard", "same_week", "same_day"]
    policy_risk: Literal["low", "medium", "high"]
    requires_manager_approval: bool
    notes: str

    @field_validator("category")
    @classmethod
    def category_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("category must not be empty")
        return v.strip()


class VerifierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_score: int = Field(ge=0, le=100)
    issues: list[str]
    is_acceptable: bool
