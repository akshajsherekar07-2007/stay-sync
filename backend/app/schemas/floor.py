"""Pydantic schemas for floor endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────


class FloorCreate(BaseModel):
    """Request body for creating a floor."""

    floor_number: int
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    sort_order: int = 0


class FloorUpdate(BaseModel):
    """PATCH body for updating a floor — all fields optional."""

    floor_number: int | None = None
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    sort_order: int | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class FloorRead(BaseModel):
    """Response DTO for a floor."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    floor_number: int
    name: str | None
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
