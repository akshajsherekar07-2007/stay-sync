"""Pydantic schemas for image endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────


class ImageReorderItem(BaseModel):
    """A single item in the reorder list."""

    id: uuid.UUID
    sort_order: int = Field(..., ge=0)


class ImageReorder(BaseModel):
    """Request body for reordering images."""

    images: list[ImageReorderItem] = Field(
        ...,
        min_length=1,
        description="List of image IDs with their new sort order.",
    )


class ImageUpdate(BaseModel):
    """PATCH body for updating image metadata."""

    alt_text: str | None = Field(default=None, max_length=255)
    is_primary: bool | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class ImageRead(BaseModel):
    """Response DTO for an image."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    property_id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int
    is_primary: bool
    file_size_bytes: int | None
    mime_type: str | None
    created_at: datetime
