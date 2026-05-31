"""Room ORM model.

Maps to the ``rooms`` table (Phase 1 — Table 3.6 in DATABASE_SCHEMA.md).

A Room belongs to a Floor and contains one or more Beds.
The room_number must be unique within its Floor (partial unique index).

Rooms carry pricing and sharing-type information that applies to all beds
within them unless a bed overrides the price individually.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.bed import Bed
    from app.models.floor import Floor
    from app.models.property import Property


class Room(TimestampedBase):
    """A physical room within a floor of a property.

    Columns
    -------
    floor_id         : FK → floors.id
    property_id      : FK → properties.id (denormalized for query convenience)
    room_number      : Alphanumeric room identifier (e.g., "101", "A2")
    name             : Human-readable label (e.g., "Deluxe Double")
    sharing_type     : One of ``single`` | ``double`` | ``triple`` | ``quad``
    price_per_bed    : Monthly price per bed (Decimal, 2 dp)
    description      : Optional long-form room description
    has_attached_bath: Whether room has an en-suite bathroom
    has_ac           : Air conditioning
    has_balcony      : Balcony access
    sort_order       : Display order within the floor

    Constraints
    -----------
    (floor_id, room_number) unique per non-deleted row.

    Relationships
    -------------
    floor    : Many-to-one → floors (back_populates="rooms")
    property : Many-to-one → properties (informational, no cascade)
    beds     : One-to-many → beds (back_populates="room")
    """

    __tablename__ = "rooms"

    __table_args__ = (
        Index(
            "idx_rooms_floor_id",
            "floor_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_rooms_property_id",
            "property_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_rooms_floor_number",
            "floor_id",
            "room_number",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_rooms_sharing_type", "sharing_type"),
        Index("idx_rooms_price", "price_per_bed"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    floor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("floors.id", ondelete="CASCADE"),
        nullable=False,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    room_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    sharing_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    price_per_bed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    has_attached_bath: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    has_ac: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    has_balcony: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    floor: Mapped[Floor] = relationship(
        "Floor",
        back_populates="rooms",
        lazy="select",
    )

    property: Mapped[Property] = relationship(
        "Property",
        lazy="select",
        foreign_keys=[property_id],
    )

    beds: Mapped[list[Bed]] = relationship(
        "Bed",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Bed.sort_order",
    )

    def __repr__(self) -> str:
        return (
            f"<Room id={self.id!s:.8} room_number={self.room_number!r}"
            f" floor_id={self.floor_id!s:.8}>"
        )
