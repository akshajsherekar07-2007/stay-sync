"""Pydantic schemas for amenity endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────


class AmenityAttach(BaseModel):
    """Request body for attaching amenities to a property."""

    amenity_ids: list[uuid.UUID] = Field(
        ...,
        min_length=1,
        description="List of amenity UUIDs to attach to the property.",
    )


# ── Response schemas ──────────────────────────────────────────────────────────


class AmenityRead(BaseModel):
    """Response DTO for an amenity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    icon: str | None
    category: str | None
