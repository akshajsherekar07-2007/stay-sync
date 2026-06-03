"""Auth request and response schemas.

All Pydantic DTOs for authentication endpoints.  Never expose ORM models
directly in API responses — use these schemas instead.

Schemas
-------
RegisterRequest   — POST /auth/register body
LoginRequest      — POST /auth/login body
TokenResponse     — Access token payload embedded in login/refresh responses
LoginResponse     — Full login response (token + user snapshot)
RefreshResponse   — Token refresh response
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import UserRole


# ── Request schemas ───────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr = Field(
        ...,
        description="Unique email address for this account.",
        examples=["student@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must contain uppercase and digit).",
        examples=["SecurePass1"],
    )
    role: UserRole = Field(
        ...,
        description="Account role: student or owner.",
        examples=["student"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Display name shown across the platform.",
        examples=["Rohan Sharma"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce: ≥1 uppercase letter and ≥1 digit."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role_not_admin(cls, v: UserRole) -> UserRole:
        """Prevent self-registration as admin."""
        if v == UserRole.ADMIN:
            raise ValueError("Admin accounts cannot be self-registered.")
        return v


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(
        ...,
        description="Registered email address.",
        examples=["student@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password.",
    )


# ── Response schemas ──────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    """Access token data returned on login and refresh."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(
        ...,
        description="Signed JWT access token (HS256). Valid for 15 minutes.",
    )
    token_type: str = Field(
        default="bearer",
        description="Always 'bearer'.",
    )
    expires_in: int = Field(
        ...,
        description="Seconds until the access token expires.",
        examples=[900],
    )


class LoginResponse(BaseModel):
    """Full response returned on successful login or registration."""

    model_config = ConfigDict(from_attributes=True)

    token: TokenResponse
    user_id: str = Field(..., description="UUID of the authenticated user.")
    email: str = Field(..., description="Email address of the authenticated user.")
    role: str = Field(..., description="Role of the authenticated user.")
    full_name: str | None = Field(
        default=None,
        description="Display name from the user's profile.",
    )
