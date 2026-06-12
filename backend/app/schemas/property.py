"""Pydantic schemas for property endpoints.

Request / response DTOs for property CRUD, listing, filtering, and detail views.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import GenderPreference, PropertyStatus, PropertyType


# ── Request schemas ───────────────────────────────────────────────────────────


class PropertyCreate(BaseModel):
    """Request body for creating a property."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    property_type: PropertyType
    gender_preference: GenderPreference = GenderPreference.COED
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    pincode: str = Field(..., min_length=1, max_length=10)
    country: str = Field(default="India", max_length=100)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    google_place_id: str | None = Field(default=None, max_length=255)
    place_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    rules: str | None = Field(default=None, max_length=5000)


class PropertyUpdate(BaseModel):
    """PATCH body for updating a property — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    property_type: PropertyType | None = None
    gender_preference: GenderPreference | None = None
    address_line1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    pincode: str | None = Field(default=None, min_length=1, max_length=10)
    country: str | None = Field(default=None, max_length=100)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    google_place_id: str | None = Field(default=None, max_length=255)
    place_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=255)
    rules: str | None = Field(default=None, max_length=5000)


class PropertyStatusUpdate(BaseModel):
    """Request body for changing property status."""

    status: PropertyStatus


# ── Filter / query schemas ────────────────────────────────────────────────────


class PropertyFilter(BaseModel):
    """Query parameters for property listing endpoint."""

    city: str | None = None
    state: str | None = None
    property_type: PropertyType | None = None
    gender_preference: GenderPreference | None = None
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    status: PropertyStatus | None = None
    search: str | None = Field(default=None, max_length=255)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ── Response schemas ──────────────────────────────────────────────────────────


class PropertyRead(BaseModel):
    """Response DTO for a single property (no nested hierarchy)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    property_type: str
    gender_preference: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    pincode: str
    country: str
    latitude: Decimal | None
    longitude: Decimal | None
    google_place_id: str | None
    place_name: str | None
    contact_phone: str | None
    contact_email: str | None
    min_price: Decimal | None
    max_price: Decimal | None
    total_beds: int
    available_beds: int
    status: str
    is_verified: bool
    last_refreshed_at: datetime | None
    rules: str | None
    created_at: datetime
    updated_at: datetime


class PropertyListItem(BaseModel):
    """Lightweight DTO for paginated property listings."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    property_type: str
    gender_preference: str
    city: str
    state: str
    pincode: str
    min_price: Decimal | None
    max_price: Decimal | None
    total_beds: int
    available_beds: int
    status: str
    is_verified: bool
    created_at: datetime
    # primary image URL (populated by service layer)
    primary_image_url: str | None = None
    is_saved: bool = False
