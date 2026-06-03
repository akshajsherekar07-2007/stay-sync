"""RefreshToken ORM model.

Maps to the ``refresh_tokens`` table (Phase 1.4 — Table 3.3 in DATABASE_SCHEMA.md).

Stores hashed refresh tokens for JWT refresh token rotation.  The raw token
is never persisted — only its SHA-256 hash is stored.  The raw token is
delivered to the client via an HttpOnly cookie.

This model inherits from ``Base`` (not ``TimestampedBase``) because the
``refresh_tokens`` table has no ``updated_at`` or ``deleted_at`` columns.
Invalidation uses ``revoked_at`` instead of soft-delete semantics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    """Hashed refresh token record for JWT token rotation.

    Inherits directly from ``Base`` (not ``TimestampedBase``) because this
    table omits ``updated_at`` and ``deleted_at`` by design — the schema
    uses ``revoked_at`` for invalidation and has no soft-delete semantics.

    Columns
    -------
    id           : UUID v4 primary key
    user_id      : FK → users.id — owner of the token
    token_hash   : SHA-256 hash of the raw token (UNIQUE)
    device_info  : Optional user-agent / device description for display
    ip_address   : Client IP at time of issuance (IPv4 or IPv6, max 45 chars)
    expires_at   : Absolute expiry timestamp (UTC)
    revoked_at   : Set when the token is invalidated; NULL = still valid
    created_at   : Issuance timestamp
    """

    __tablename__ = "refresh_tokens"

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_hash", "token_hash", unique=True),
        Index("idx_refresh_tokens_expires", "expires_at"),
    )

    # ── Columns ──────────────────────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    device_info: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped[User] = relationship(
        "User",
        lazy="select",
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def is_valid(self) -> bool:
        """Return True if the token is neither revoked nor expired."""
        from datetime import timezone

        now = datetime.now(tz=timezone.utc)
        return self.revoked_at is None and self.expires_at > now

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id!s:.8} user_id={self.user_id!s:.8}"
            f" revoked={self.revoked_at is not None}>"
        )
