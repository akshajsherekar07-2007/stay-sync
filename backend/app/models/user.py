"""User ORM model.

Maps to the ``users`` table (Phase 1 — Table 3.1 in DATABASE_SCHEMA.md).

Stores core authentication identity: email, password hash, role,
verification flags, and activity status.  Extended profile data lives
in the ``profiles`` table (one-to-one relationship).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.property import Property


class User(TimestampedBase):
    """Authentication and identity record for all platform users.

    Columns
    -------
    email               : Unique email address (case-sensitive, max 255 chars)
    phone               : Optional unique phone number (max 20 chars)
    password_hash       : bcrypt hash — never stored in plaintext
    role                : One of ``student`` | ``owner`` | ``admin``
    is_email_verified   : Flag — must be True before hold requests are allowed
    is_phone_verified   : Flag
    is_active           : Soft-disable without deletion
    last_login_at       : UTC timestamp of most recent successful login

    Relationships
    -------------
    profile     : One-to-one → profiles (back_populates="user")
    properties  : One-to-many → properties (back_populates="owner")
    """

    __tablename__ = "users"

    __table_args__ = (
        # Partial unique indexes — only enforce uniqueness for non-deleted rows.
        # SQLAlchemy renders these but Alembic autogenerate also picks them up
        # because they are declared on the mapper.
        Index(
            "idx_users_email",
            "email",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index(
            "idx_users_phone",
            "phone",
            unique=True,
            postgresql_where="deleted_at IS NULL AND phone IS NOT NULL",
        ),
        Index("idx_users_role", "role"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=False,  # covered by idx_users_email above
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,  # idx_users_role — allows filtering by role
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    profile: Mapped[Profile | None] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,  # one-to-one
        cascade="all, delete-orphan",
        lazy="select",
    )

    properties: Mapped[list[Property]] = relationship(
        "Property",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s:.8} email={self.email!r} role={self.role!r}>"
