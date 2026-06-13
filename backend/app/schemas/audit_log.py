"""Pydantic schemas for audit log endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────


class AuditLogCreate(BaseModel):
    """Internal DTO for creating an audit log entry.
    
    Not exposed directly via public API; used internally by the 
    application to record immutable trails of critical actions.
    """

    user_id: uuid.UUID | None = None
    action: str = Field(..., max_length=50)
    entity_type: str = Field(..., max_length=50)
    entity_id: uuid.UUID
    old_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = None


# Note: AuditLogUpdate is deliberately omitted. Audit logs are append-only.


# ── Response schemas ──────────────────────────────────────────────────────────


class AuditLogRead(BaseModel):
    """Response DTO for an audit log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    old_data: dict[str, Any] | None
    new_data: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
