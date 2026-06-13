"""Booking ORM model.

Maps to the ``bookings`` table (Phase 2 — migration 006_hold_system).

A Booking represents a confirmed occupancy of a bed by a student.
Bookings are created after a hold is approved and the student confirms,
or when an owner assigns a bed directly via override.

Only one active (status='confirmed') booking is allowed per bed at a
time, enforced by the partial unique index ``idx_bookings_active_bed``.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import BookingStatus
from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.bed import Bed
    from app.models.hold_request import HoldRequest
    from app.models.property import Property
    from app.models.user import User


class Booking(TimestampedBase):
    """Confirmed bed occupancy record.

    Columns
    -------
    bed_id           : FK → beds.id
    student_id       : FK → users.id
    property_id      : FK → properties.id (denormalized)
    hold_request_id  : FK → hold_requests.id (nullable — direct bookings have no hold)
    status           : confirmed | vacated | cancelled
    check_in_date    : Planned or actual check-in date
    check_out_date   : Planned or actual check-out date
    confirmed_at     : Timestamp when the booking was confirmed
    vacated_at       : Timestamp when the student vacated the bed
    notes            : Optional free-text notes

    Relationships
    -------------
    bed          : Many-to-one → beds
    student      : Many-to-one → users
    property     : Many-to-one → properties
    hold_request : Many-to-one → hold_requests (optional)
    """

    __tablename__ = "bookings"

    # Indexes are created in migration 006; no __table_args__ needed here.

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

    hold_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hold_requests.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BookingStatus.CONFIRMED.value,
        server_default=BookingStatus.CONFIRMED.value,
    )

    check_in_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
    )

    check_out_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
    )

    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )

    vacated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    notes: Mapped[str | None] = mapped_column(
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

    hold_request: Mapped[HoldRequest | None] = relationship(
        "HoldRequest",
        back_populates="booking",
        lazy="select",
        foreign_keys=[hold_request_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id!s:.8} bed={self.bed_id!s:.8}"
            f" student={self.student_id!s:.8} status={self.status!r}>"
        )
