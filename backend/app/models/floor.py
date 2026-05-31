"""Floor ORM model.

Maps to the ``floors`` table (Phase 1 — Table 3.5 in DATABASE_SCHEMA.md).

A Floor represents a physical floor within a Property.  The hierarchy is:
    Property → Floor → Room → Bed

Each Floor has an integer ``floor_number`` which must be unique *per property*
(enforced by a partial unique index).  Floors are ordered by ``sort_order``
for display purposes.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.property import Property
    from app.models.room import Room


class Floor(TimestampedBase):
    """A physical floor level within a property.

    Columns
    -------
    property_id  : FK → properties.id
    floor_number : Integer floor number (0 = ground, negative = basement)
    name         : Human-readable label (e.g., "Ground Floor", "Basement")
    description  : Optional description
    sort_order   : Display ordering within the property listing

    Constraints
    -----------
    (property_id, floor_number) must be unique per non-deleted row.

    Relationships
    -------------
    property : Many-to-one → properties (back_populates="floors")
    rooms    : One-to-many → rooms (back_populates="floor")
    """

    __tablename__ = "floors"

    __table_args__ = (
        Index(
            "idx_floors_property_id",
            "property_id",
            postgresql_where="deleted_at IS NULL",
        ),
        # Partial unique index — floor_number unique per property for active rows
        Index(
            "idx_floors_property_number",
            "property_id",
            "floor_number",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    floor_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    property: Mapped[Property] = relationship(
        "Property",
        back_populates="floors",
        lazy="select",
    )

    rooms: Mapped[list[Room]] = relationship(
        "Room",
        back_populates="floor",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Room.sort_order",
    )

    def __repr__(self) -> str:
        return (
            f"<Floor id={self.id!s:.8} floor_number={self.floor_number}"
            f" property_id={self.property_id!s:.8}>"
        )
