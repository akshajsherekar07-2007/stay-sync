"""Pydantic schemas for bed endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────


class BedCreate(BaseModel):
    """Request body for creating a bed."""

    bed_number: str = Field(..., min_length=1, max_length=10)
    label: str | None = Field(default=None, max_length=50)
    price: Decimal | None = Field(default=None, gt=0)
    sort_order: int = 0


class BedUpdate(BaseModel):
    """PATCH body for updating a bed — all fields optional."""

    bed_number: str | None = Field(default=None, min_length=1, max_length=10)
    label: str | None = Field(default=None, max_length=50)
    price: Decimal | None = Field(default=None, gt=0)
    sort_order: int | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class BedRead(BaseModel):
    """Response DTO for a bed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_id: uuid.UUID
    property_id: uuid.UUID
    bed_number: str
    label: str | None
    status: str
    price: Decimal | None
    version: int
    sort_order: int
    created_at: datetime
    updated_at: datetime
