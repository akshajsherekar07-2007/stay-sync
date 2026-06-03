"""User and profile Pydantic DTOs.

Never return ORM model instances from API endpoints — map them through
these schemas first.

Schemas
-------
ProfileRead     — Profile data embedded in user responses
UserRead        — Full user record (with nested profile)
MeResponse      — Current user response (alias for UserRead)
ProfileUpdate   — PATCH /users/me/profile body (all fields optional)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Profile schemas ───────────────────────────────────────────────────────────


class ProfileRead(BaseModel):
    """Profile data as returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    full_name: str = Field(..., description="Display name.")
    avatar_url: str | None = Field(default=None, description="Avatar image URL.")
    bio: str | None = Field(default=None, description="Short self-description.")
    college_name: str | None = Field(
        default=None,
        description="Student's college name (student users only).",
    )
    city: str | None = Field(default=None, description="City.")
    state: str | None = Field(default=None, description="State / province.")
    date_of_birth: date | None = Field(default=None, description="Date of birth.")


class ProfileUpdate(BaseModel):
    """PATCH body for updating the current user's profile.

    All fields are optional — only provided fields are updated (PATCH semantics).
    """

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Display name.",
    )
    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Avatar image URL.",
    )
    bio: str | None = Field(
        default=None,
        max_length=1000,
        description="Short self-description.",
    )
    college_name: str | None = Field(
        default=None,
        max_length=255,
        description="College name (student users only).",
    )
    city: str | None = Field(
        default=None,
        max_length=100,
        description="City.",
    )
    state: str | None = Field(
        default=None,
        max_length=100,
        description="State / province.",
    )
    date_of_birth: date | None = Field(
        default=None,
        description="Date of birth (YYYY-MM-DD).",
    )


# ── User schemas ──────────────────────────────────────────────────────────────


class UserRead(BaseModel):
    """Full user record as returned by GET /users/me.

    Includes the nested profile if one exists.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="User UUID.")
    email: str = Field(..., description="Email address.")
    role: str = Field(..., description="Role: student, owner, or admin.")
    is_email_verified: bool = Field(
        ...,
        description="Whether the email address has been verified.",
    )
    is_active: bool = Field(..., description="Whether the account is active.")
    last_login_at: datetime | None = Field(
        default=None,
        description="Timestamp of the most recent successful login.",
    )
    created_at: datetime = Field(..., description="Account creation timestamp.")
    profile: ProfileRead | None = Field(
        default=None,
        description="Extended profile data (null if profile not yet created).",
    )


# MeResponse is a semantic alias for UserRead used on the /me endpoint
MeResponse = UserRead
