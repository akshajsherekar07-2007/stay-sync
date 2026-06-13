"""Pydantic schemas for booking endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import BookingStatus


# ── Request schemas ───────────────────────────────────────────────────────────


class BookingCreate(BaseModel):
    """Request body for creating a booking.
    
    Usually created by converting an approved hold request, but owners
    can also create direct bookings via overrides.
    """

    bed_id: uuid.UUID
    hold_request_id: uuid.UUID | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> BookingCreate:
        if self.check_in_date and self.check_out_date:
            if self.check_in_date > self.check_out_date:
                raise ValueError("check_out_date cannot be earlier than check_in_date")
        return self


class BookingUpdate(BaseModel):
    """PATCH body for updating a booking."""

    status: BookingStatus | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> BookingUpdate:
        if self.check_in_date and self.check_out_date:
            if self.check_in_date > self.check_out_date:
                raise ValueError("check_out_date cannot be earlier than check_in_date")
        return self


# ── Response schemas ──────────────────────────────────────────────────────────


class BookingRead(BaseModel):
    """Response DTO for a booking."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bed_id: uuid.UUID
    student_id: uuid.UUID
    property_id: uuid.UUID
    hold_request_id: uuid.UUID | None
    status: BookingStatus
    check_in_date: date | None
    check_out_date: date | None
    confirmed_at: datetime
    vacated_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
