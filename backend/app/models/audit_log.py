"""AuditLog ORM model.

Maps to the ``audit_logs`` table (Phase 2 — migration 007_notifications_audit).

Provides an append-only audit trail for all hold, booking, and system
state changes.  Records are never updated or deleted.

This model inherits from ``Base`` (not ``TimestampedBase``) because the
``audit_logs`` table has no ``updated_at`` or ``deleted_at`` columns.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Append-only audit trail record.

    Inherits from ``Base`` (not ``TimestampedBase``) because this table
    is strictly append-only — no updates, no soft-deletes.

    Columns
    -------
    id          : UUID v4 primary key
    user_id     : FK → users.id (nullable — system-initiated actions)
    action      : Action performed (e.g., 'hold_approved', 'booking_confirmed')
    entity_type : Type of entity affected (e.g., 'hold_request', 'booking')
    entity_id   : UUID of the affected entity
    old_data    : JSONB snapshot of the entity before the change
    new_data    : JSONB snapshot of the entity after the change
    ip_address  : Client IP at time of action (IPv4 or IPv6, max 45 chars)
    user_agent  : Client user-agent string
    created_at  : Timestamp of the audit event

    Relationships
    -------------
    user : Many-to-one → users (nullable)
    """

    __tablename__ = "audit_logs"

    # Indexes are created in migration 007; no __table_args__ needed here.

    # ── Columns ──────────────────────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    old_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )

    new_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped[User | None] = relationship(
        "User",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id!s:.8} action={self.action!r}"
            f" entity={self.entity_type}:{self.entity_id!s:.8}>"
        )
