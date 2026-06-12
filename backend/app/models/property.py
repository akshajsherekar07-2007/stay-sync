"""Property ORM model.

Maps to the ``properties`` table (Phase 1 — Table 3.4 in DATABASE_SCHEMA.md).

A Property is the top-level accommodation listing created by an Owner.
The hierarchy below it is: Property → Floor → Room → Bed.

Location data supports both free-text address and geo-coordinates for
future PostGIS distance-based search (Phase 3).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.floor import Floor
    from app.models.property_amenity import PropertyAmenity
    from app.models.property_image import PropertyImage
    from app.models.user import User


class Property(TimestampedBase):
    """Accommodation listing owned and managed by an Owner user.

    Columns
    -------
    owner_id          : FK → users.id (must have role='owner')
    name              : Display name of the property
    description       : Long-form HTML-safe description
    property_type     : One of ``pg`` | ``hostel`` | ``flat`` | ``apartment``
    gender_preference : One of ``male`` | ``female`` | ``coed`` (default: coed)
    address_line1     : Street address
    address_line2     : Apartment / suite number (optional)
    city              : City — indexed for location filtering
    state             : State / province
    pincode           : Postal / zip code
    country           : Country (default: India)
    latitude          : Decimal(10,7) — for geo queries
    longitude         : Decimal(10,7) — for geo queries
    google_place_id   : Google Maps Place ID (optional, for future Maps integration)
    place_name        : Formatted place name from Maps API
    contact_phone     : Owner contact phone shown to verified students
    contact_email     : Owner contact email
    min_price         : Lowest bed price (computed or manually set)
    max_price         : Highest bed price
    total_beds        : Maintained by DB trigger (sync_property_bed_counts)
    available_beds    : Maintained by DB trigger
    status            : One of ``draft`` | ``pending_review`` | ``active`` |
                        ``inactive`` | ``suspended`` (default: draft)
    is_verified       : Set by admin once property has been reviewed
    last_refreshed_at : Owner confirms listing is still accurate
    rules             : House rules text

    Relationships
    -------------
    owner  : Many-to-one → users (back_populates="properties")
    floors : One-to-many → floors (back_populates="property")
    """

    __tablename__ = "properties"

    __table_args__ = (
        Index("idx_properties_owner_id", "owner_id"),
        Index("idx_properties_city", "city"),
        Index(
            "idx_properties_status",
            "status",
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_properties_type", "property_type"),
        Index("idx_properties_gender", "gender_preference"),
        Index("idx_properties_price", "min_price", "max_price"),
        Index(
            "idx_properties_available",
            "available_beds",
            postgresql_where="deleted_at IS NULL AND status = 'active'",
        ),
        # NOTE: The PostGIS GIST index (idx_properties_location) is created
        # in the Alembic migration using op.execute() because SQLAlchemy's
        # Index() does not support arbitrary GIST expressions natively.
    )

    # ── Identity ─────────────────────────────────────────────────────────────

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # ── Classification ───────────────────────────────────────────────────────

    property_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    gender_preference: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="coed",
        server_default="coed",
    )

    # ── Location ─────────────────────────────────────────────────────────────

    address_line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="India",
        server_default="India",
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        default=None,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        default=None,
    )

    google_place_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    place_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    # ── Contact ──────────────────────────────────────────────────────────────

    contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    # ── Pricing ──────────────────────────────────────────────────────────────

    min_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        default=None,
    )

    max_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        default=None,
    )

    # ── Inventory counts (maintained by DB trigger) ───────────────────────────

    total_beds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    available_beds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # ── Status ───────────────────────────────────────────────────────────────

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    rules: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    owner: Mapped[User] = relationship(
        "User",
        back_populates="properties",
        lazy="select",
    )

    floors: Mapped[list[Floor]] = relationship(
        "Floor",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Floor.sort_order",
    )

    property_amenities: Mapped[list[PropertyAmenity]] = relationship(
        "PropertyAmenity",
        cascade="all, delete-orphan",
        lazy="select",
    )

    images: Mapped[list[PropertyImage]] = relationship(
        "PropertyImage",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="PropertyImage.sort_order",
    )

    def __repr__(self) -> str:
        return (
            f"<Property id={self.id!s:.8} name={self.name!r}"
            f" status={self.status!r}>"
        )
