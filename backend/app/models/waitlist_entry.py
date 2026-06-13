"""WaitlistEntry ORM model.

Maps to the ``waitlist_entries`` table (Phase 2 — migration 006_hold_system).

When a student requests a hold on a bed that is already held or occupied,
they are placed in a FIFO waitlist queue.  When the current hold expires
or is cancelled, the next student in the queue is automatically promoted
to a new AUTO-APPROVED hold with a 24-hour default expiry.

The ``position`` column determines queue order (lower = closer to front).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import WaitlistStatus
from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.bed import Bed
    from app.models.property import Property
    from app.models.user import User


class WaitlistEntry(TimestampedBase):
    """A student's position in the bed waitlist queue.

    Columns
    -------
    bed_id       : FK → beds.id
    student_id   : FK → users.id
    property_id  : FK → properties.id (denormalized)
    position     : Queue position (1 = next in line)
    status       : active | promoted | expired | cancelled
    joined_at    : Timestamp when the student joined the queue
    promoted_at  : Timestamp when the student was promoted to a hold
    cancelled_at : Timestamp when the student cancelled or was removed

    Relationships
    -------------
    bed      : Many-to-one → beds
    student  : Many-to-one → users
    property : Many-to-one → properties
    """

    __tablename__ = "waitlist_entries"

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

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WaitlistStatus.ACTIVE.value,
        server_default=WaitlistStatus.ACTIVE.value,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )

    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    def __repr__(self) -> str:
        return (
            f"<WaitlistEntry id={self.id!s:.8} bed={self.bed_id!s:.8}"
            f" student={self.student_id!s:.8} position={self.position}>"
        )
