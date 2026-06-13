"""Bed ORM model.

Maps to the ``beds`` table (Phase 1 — Table 3.7 in DATABASE_SCHEMA.md).

The Bed is the **atomic unit of inventory** in StaySync.  All holds and
bookings target a specific bed, not a room or property.

Key design decisions for Phase 1
---------------------------------
* ``status`` defaults to ``'vacant'`` and cycles through the bed state machine.
* ``version`` is the optimistic-lock counter — always increment on status change.
* ``current_hold_id`` and ``current_booking_id`` columns are present (per schema)
  but the FK constraints pointing to Phase 2 tables (hold_requests, bookings)
  are NOT added in this migration.  They will be added via migration
  ``008_bed_fk_updates`` in Phase 2.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.hold_request import HoldRequest
    from app.models.property import Property
    from app.models.room import Room


class Bed(TimestampedBase):
    """A single bed slot — the atomic unit targeted by holds and bookings.

    Columns
    -------
    room_id             : FK → rooms.id
    property_id         : FK → properties.id (denormalized)
    bed_number          : Short identifier within the room (e.g., "A", "1")
    label               : Human-readable label (e.g., "Upper Bunk", "Window Bed")
    status              : ``vacant`` | ``held`` | ``occupied``
    price               : Optional per-bed price override (uses room price if NULL)
    current_hold_id     : UUID of active hold — FK added in Phase 2 migration
    current_booking_id  : UUID of active booking — FK added in Phase 2 migration
    version             : Optimistic-lock counter (increment on every state change)
    sort_order          : Display order within the room

    Constraints
    -----------
    (room_id, bed_number) unique per non-deleted row.

    Relationships
    -------------
    room     : Many-to-one → rooms (back_populates="beds")
    property : Many-to-one → properties (informational)
    """

    __tablename__ = "beds"

    __table_args__ = (
        Index(
            "idx_beds_room_id",
            "room_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_beds_property_id",
            "property_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_beds_status",
            "status",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_beds_room_number",
            "room_id",
            "bed_number",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    bed_number: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="vacant",
        server_default="vacant",
    )

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        default=None,
    )

    # Phase 2 FK targets — FK constraints added via migration 008
    current_hold_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hold_requests.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    current_booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    room: Mapped[Room] = relationship(
        "Room",
        back_populates="beds",
        lazy="select",
    )

    property: Mapped[Property] = relationship(
        "Property",
        lazy="select",
        foreign_keys=[property_id],
    )

    current_hold: Mapped[HoldRequest | None] = relationship(
        "HoldRequest",
        lazy="select",
        foreign_keys=[current_hold_id],
    )

    current_booking: Mapped[Booking | None] = relationship(
        "Booking",
        lazy="select",
        foreign_keys=[current_booking_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Bed id={self.id!s:.8} bed_number={self.bed_number!r}"
            f" status={self.status!r} version={self.version}>"
        )
