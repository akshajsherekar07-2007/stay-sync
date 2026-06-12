"""Pydantic schemas for room endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SharingType


# ── Request schemas ───────────────────────────────────────────────────────────


class RoomCreate(BaseModel):
    """Request body for creating a room."""

    room_number: str = Field(..., min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    sharing_type: SharingType
    price_per_bed: Decimal = Field(..., gt=0)
    description: str | None = Field(default=None, max_length=2000)
    has_attached_bath: bool = False
    has_ac: bool = False
    has_balcony: bool = False
    sort_order: int = 0


class RoomUpdate(BaseModel):
    """PATCH body for updating a room — all fields optional."""

    room_number: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    sharing_type: SharingType | None = None
    price_per_bed: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=2000)
    has_attached_bath: bool | None = None
    has_ac: bool | None = None
    has_balcony: bool | None = None
    sort_order: int | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class RoomRead(BaseModel):
    """Response DTO for a room."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID
    property_id: uuid.UUID
    room_number: str
    name: str | None
    sharing_type: str
    price_per_bed: Decimal
    description: str | None
    has_attached_bath: bool
    has_ac: bool
    has_balcony: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
