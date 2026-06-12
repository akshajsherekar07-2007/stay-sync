"""PropertyAmenity ORM model (junction table).

Maps to the ``property_amenities`` table (Phase 1 — Table 3.9 in DATABASE_SCHEMA.md).

Many-to-many link between properties and amenities.
No ``updated_at`` or ``deleted_at`` — rows are inserted/deleted, never updated.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PropertyAmenity(Base):
    """Junction row linking a property to an amenity.

    Columns
    -------
    id          : UUID primary key
    property_id : FK → properties.id
    amenity_id  : FK → amenities.id
    created_at  : Insertion timestamp

    Constraints
    -----------
    (property_id, amenity_id) must be unique.
    """

    __tablename__ = "property_amenities"

    __table_args__ = (
        Index(
            "idx_property_amenities_unique",
            "property_id",
            "amenity_id",
            unique=True,
        ),
        Index(
            "idx_property_amenities_property",
            "property_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    amenity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("amenities.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<PropertyAmenity property_id={self.property_id!s:.8}"
            f" amenity_id={self.amenity_id!s:.8}>"
        )
