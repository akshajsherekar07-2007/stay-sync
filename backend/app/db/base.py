"""SQLAlchemy declarative base for all ORM models.

Provides a shared ``TimestampedBase`` that every model inherits.
It wires up:
  - UUID v4 primary key
  - created_at / updated_at auto-managed timestamps
  - soft-delete deleted_at column

All tables also use ``__table_args__`` to specify any index or
constraint overrides at the model level.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base — shared metadata registry."""


class TimestampedBase(Base):
    """Abstract base that every StaySync ORM model inherits.

    Columns added to every table
    ----------------------------
    id          : UUID v4 primary key (server-default via gen_random_uuid())
    created_at  : TIMESTAMPTZ — set once on INSERT via DB default
    updated_at  : TIMESTAMPTZ — updated by application / DB trigger on every UPDATE
    deleted_at  : TIMESTAMPTZ — NULL means active; non-NULL means soft-deleted
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = datetime.utcnow()

    @property
    def is_deleted(self) -> bool:
        """Return True if this record has been soft-deleted."""
        return self.deleted_at is not None
