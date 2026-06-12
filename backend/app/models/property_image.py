"""PropertyImage ORM model.

Maps to the ``property_images`` table (Phase 1 — Table 3.10 in DATABASE_SCHEMA.md).

Stores image metadata for properties, floors, rooms, and beds.  The actual
files live in Supabase Storage; this table holds the reference URL and path.
Has ``deleted_at`` for soft-delete but no ``updated_at``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PropertyImage(Base):
    """An image attached to a property, floor, room, or bed.

    Columns
    -------
    id             : UUID primary key
    entity_type    : The type of entity this image belongs to (property/floor/room/bed)
    entity_id      : The UUID of the entity
    property_id    : FK → properties.id (always set for easy property-level queries)
    url            : Public URL of the image
    storage_path   : Supabase Storage path for deletion
    alt_text       : Accessibility text
    sort_order     : Display order
    is_primary     : Whether this is the primary/cover image
    file_size_bytes: File size in bytes
    mime_type      : MIME type (e.g., image/jpeg)
    created_at     : Insertion timestamp
    deleted_at     : Soft-delete marker
    """

    __tablename__ = "property_images"

    __table_args__ = (
        Index(
            "idx_images_entity",
            "entity_type",
            "entity_id",
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_images_property",
            "property_id",
            postgresql_where="deleted_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    alt_text: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        return (
            f"<PropertyImage id={self.id!s:.8}"
            f" entity_type={self.entity_type!r}"
            f" property_id={self.property_id!s:.8}>"
        )
