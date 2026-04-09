"""
End-of-module exercise (learner completes the schema).

**Suggested prompt theme:** software access request.

Fill in missing fields on :class:`SoftwareAccessRequestExercise` (``TODO`` markers).
Then add an extractor and tests patterned on ``structured_outputs_tutorial.pipelines``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SoftwareAccessRequestExercise(BaseModel):
    """
    Internal access ticket — incomplete on purpose.

    TODO (learner): add at least:
      - requested_system: str
      - access_level: Literal["read", "write", "admin"] or similar
      - business_reason: str
      - manager_approval_required: bool
    """

    model_config = ConfigDict(extra="forbid")

    employee_name: str = Field(description="Person requesting access.")

    # TODO: requested_system: str
    # TODO: access_level: ...
    # TODO: business_reason: str
    # TODO: manager_approval_required: bool
