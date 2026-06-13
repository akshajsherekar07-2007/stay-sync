"""Pydantic schemas for hold request endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import HoldStatus


# ── Request schemas ───────────────────────────────────────────────────────────


class HoldRequestCreate(BaseModel):
    """Request body for creating a hold on a bed.
    
    The student_id is inferred from the authenticated user, and the 
    property_id is inferred from the targeted bed.
    """

    bed_id: uuid.UUID
    hold_duration_hours: int = Field(
        default=24,
        ge=1,
        le=72,
        description="Duration in hours to hold the bed. Min 1, Max 72.",
    )


class HoldRequestUpdate(BaseModel):
    """PATCH body for updating a hold request.
    
    Primarily used by owners to approve or reject a hold, or by students
    to cancel their own hold.
    """

    status: HoldStatus | None = None
    resolution_note: str | None = Field(default=None, max_length=1000)


# ── Response schemas ──────────────────────────────────────────────────────────


class HoldRequestRead(BaseModel):
    """Response DTO for a hold request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bed_id: uuid.UUID
    student_id: uuid.UUID
    property_id: uuid.UUID
    status: HoldStatus
    hold_duration_hours: int
    requested_at: datetime
    approved_at: datetime | None
    expires_at: datetime | None
    resolved_at: datetime | None
    resolved_by: uuid.UUID | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
