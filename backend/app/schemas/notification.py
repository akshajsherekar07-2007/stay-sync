"""Pydantic schemas for notification endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import NotificationType


# ── Request schemas ───────────────────────────────────────────────────────────


class NotificationCreate(BaseModel):
    """Internal DTO for creating a notification.
    
    Not exposed directly via public API; used by the service layer
    when generating system notifications.
    """

    user_id: uuid.UUID
    type: NotificationType
    title: str = Field(..., max_length=255)
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    """PATCH body for updating a notification.
    
    Notifications are immutable; only the read status can be updated.
    """

    is_read: bool | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class NotificationRead(BaseModel):
    """Response DTO for a notification."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    data: dict[str, Any] | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime
