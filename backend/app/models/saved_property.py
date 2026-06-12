"""SavedProperty ORM model.

Maps to the ``saved_properties`` table (Phase 1 — Table 3.16 in DATABASE_SCHEMA.md).

Student wishlist / saved properties.  No ``updated_at`` or ``deleted_at`` —
rows are inserted when saving and hard-deleted when unsaving.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedProperty(Base):
    """A student's saved/bookmarked property.

    Columns
    -------
    id          : UUID primary key
    student_id  : FK → users.id
    property_id : FK → properties.id
    created_at  : Insertion timestamp

    Constraints
    -----------
    (student_id, property_id) must be unique.
    """

    __tablename__ = "saved_properties"

    __table_args__ = (
        Index(
            "idx_saved_unique",
            "student_id",
            "property_id",
            unique=True,
        ),
        Index(
            "idx_saved_student",
            "student_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<SavedProperty student_id={self.student_id!s:.8}"
            f" property_id={self.property_id!s:.8}>"
        )
