"""Pydantic schemas for waitlist entry endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import WaitlistStatus


# ── Request schemas ───────────────────────────────────────────────────────────


class WaitlistEntryCreate(BaseModel):
    """Request body for joining a bed's waitlist.
    
    The student_id is inferred from the authenticated user, and the 
    property_id is inferred from the targeted bed. Queue position is 
    calculated automatically by the service layer.
    """

    bed_id: uuid.UUID


class WaitlistEntryUpdate(BaseModel):
    """PATCH body for updating a waitlist entry.
    
    Primarily used by students to cancel their position in the queue, 
    or internally when promoting to a hold.
    """

    status: WaitlistStatus | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class WaitlistEntryRead(BaseModel):
    """Response DTO for a waitlist entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bed_id: uuid.UUID
    student_id: uuid.UUID
    property_id: uuid.UUID
    position: int
    status: WaitlistStatus
    joined_at: datetime
    promoted_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
