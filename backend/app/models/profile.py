"""Profile ORM model.

Maps to the ``profiles`` table (Phase 1 — Table 3.2 in DATABASE_SCHEMA.md).

Stores extended, user-facing information about a user.  This is a strict
one-to-one extension of ``users``: every user *may* have at most one profile.
The ``user_id`` column carries a UNIQUE constraint (partial on deleted_at).

Separation from ``users`` keeps the auth table lean and follows the principle
of separation of concerns — auth identity vs. display information.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.user import User


class Profile(TimestampedBase):
    """Extended user profile data (display name, avatar, bio, location).

    Columns
    -------
    user_id       : FK → users.id (UNIQUE — enforces one-to-one)
    full_name     : Display name shown across the platform (max 150 chars)
    avatar_url    : URL to user avatar image (Supabase Storage or external)
    bio           : Free-form self description
    college_name  : For student users — relevant to their accommodation search
    city          : City the user is located in / searching in
    state         : State / province
    date_of_birth : For identity verification purposes (future use)

    Relationships
    -------------
    user : Many-to-one → users (back_populates="profile")
    """

    __tablename__ = "profiles"

    __table_args__ = (
        Index(
            "idx_profiles_user_id",
            "user_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_profiles_city", "city"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    college_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped[User] = relationship(
        "User",
        back_populates="profile",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Profile id={self.id!s:.8} user_id={self.user_id!s:.8}"
            f" full_name={self.full_name!r}>"
        )
