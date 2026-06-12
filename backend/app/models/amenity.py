"""Amenity ORM model.

Maps to the ``amenities`` table (Phase 1 — Table 3.8 in DATABASE_SCHEMA.md).

A master catalog of amenities that can be attached to properties via the
``property_amenities`` junction table.  This table is append-only — it has
no ``updated_at`` or ``deleted_at`` columns.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Amenity(Base):
    """A single amenity entry in the master catalog.

    Columns
    -------
    id       : UUID primary key
    name     : Unique display name (e.g., "WiFi", "Parking")
    icon     : Icon identifier for frontend rendering (e.g., "wifi", "parking")
    category : Grouping category (e.g., "basic", "safety", "comfort", "facilities")
    created_at : Insertion timestamp

    Notes
    -----
    This model intentionally does NOT extend ``TimestampedBase`` because the
    amenities table has no ``updated_at`` or ``deleted_at`` columns per schema.
    """

    __tablename__ = "amenities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Amenity id={self.id!s:.8} name={self.name!r}>"
