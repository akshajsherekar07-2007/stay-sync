"""HoldRequest ORM model.

Maps to the ``hold_requests`` table (Phase 2 — migration 006_hold_system).

A HoldRequest represents a student's request to temporarily reserve a
specific bed.  The lifecycle follows:

    pending → approved → expired / cancelled
    pending → rejected
    approved → overridden (owner gives bed to another student)

Hold duration is constrained to [1, 72] hours (default 24).  Only one
active (pending/approved) hold is allowed per bed at a time, enforced
by the partial unique index ``idx_holds_active_bed``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.bed import Bed
    from app.models.property import Property
    from app.models.user import User


class HoldRequest(TimestampedBase):
    """Student hold request on a specific bed.

    Columns
    -------
    bed_id              : FK → beds.id
    student_id          : FK → users.id (requester)
    property_id         : FK → properties.id (denormalized)
    status              : pending | approved | rejected | expired | overridden | cancelled
    hold_duration_hours : Integer [1, 72], default 24
    requested_at        : Timestamp when the hold was requested
    approved_at         : Timestamp when the owner approved (NULL if not approved)
    expires_at          : Timestamp when the hold expires (set on approval)
    resolved_at         : Timestamp when the hold was resolved (rejected/expired/etc.)
    resolved_by         : FK → users.id (who resolved — owner or system)
    resolution_note     : Optional free-text note from the resolver

    Relationships
    -------------
    bed      : Many-to-one → beds
    student  : Many-to-one → users
    property : Many-to-one → properties
    resolver : Many-to-one → users (nullable)
    booking  : One-to-one  → bookings (optional, if hold was converted)
    """

    __tablename__ = "hold_requests"

    # Indexes are created in migration 006; no __table_args__ needed here
    # because all indexes use partial WHERE clauses that are migration-managed.

    # ── Columns ──────────────────────────────────────────────────────────────

    bed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("beds.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    hold_duration_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        server_default="24",
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    bed: Mapped[Bed] = relationship(
        "Bed",
        lazy="select",
        foreign_keys=[bed_id],
    )

    student: Mapped[User] = relationship(
        "User",
        lazy="select",
        foreign_keys=[student_id],
    )

    property: Mapped[Property] = relationship(
        "Property",
        lazy="select",
        foreign_keys=[property_id],
    )

    resolver: Mapped[User | None] = relationship(
        "User",
        lazy="select",
        foreign_keys=[resolved_by],
    )

    booking: Mapped[Booking | None] = relationship(
        "Booking",
        back_populates="hold_request",
        uselist=False,
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<HoldRequest id={self.id!s:.8} bed={self.bed_id!s:.8}"
            f" student={self.student_id!s:.8} status={self.status!r}>"
        )
