"""Notification ORM model.

Maps to the ``notifications`` table (Phase 2 — migration 007_notifications_audit).

Stores in-app notification records delivered to users.  Notifications are
immutable after creation — only ``is_read`` and ``read_at`` are updated.

This model inherits from ``Base`` (not ``TimestampedBase``) because the
``notifications`` table has no ``updated_at`` or ``deleted_at`` columns by design.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """In-app notification record for a user.

    Inherits from ``Base`` (not ``TimestampedBase``) because this table
    has no ``updated_at`` or ``deleted_at`` columns — notifications are
    immutable after creation, except for marking as read.

    Columns
    -------
    id         : UUID v4 primary key
    user_id    : FK → users.id — recipient
    type       : Notification type (hold_requested, hold_approved, etc.)
    title      : Short title displayed in the notification bell
    message    : Full notification message body
    data       : JSONB payload for UI rendering (default: '{}')
    is_read    : Boolean flag — toggled at the application layer
    read_at    : Timestamp when the notification was read
    created_at : Timestamp of creation

    Relationships
    -------------
    user : Many-to-one → users
    """

    __tablename__ = "notifications"

    # Indexes are created in migration 007; no __table_args__ needed here.

    # ── Columns ──────────────────────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        server_default="'{}'::jsonb",
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped[User] = relationship(
        "User",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id!s:.8} user={self.user_id!s:.8}"
            f" type={self.type!r} is_read={self.is_read}>"
        )
