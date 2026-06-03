"""RefreshToken repository — data access for the ``refresh_tokens`` table.

Note: ``RefreshToken`` inherits from ``Base`` (not ``TimestampedBase``),
so this repository does NOT extend ``BaseRepository`` which assumes
``deleted_at`` for soft-delete.  All methods are implemented directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Data access layer for the ``refresh_tokens`` table.

    Args:
        session: Active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """Persist a new refresh token record.

        Args:
            user_id:     Owner of the token.
            token_hash:  SHA-256 hash of the raw token.
            expires_at:  Absolute expiry timestamp (UTC).
            device_info: Optional device/user-agent string.
            ip_address:  Client IP address.

        Returns:
            The created ``RefreshToken`` instance.
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Look up a refresh token by its SHA-256 hash.

        Args:
            token_hash: The SHA-256 hex digest of the raw token.

        Returns:
            The matching ``RefreshToken`` or ``None``.
        """
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token_id: uuid.UUID) -> None:
        """Mark a single refresh token as revoked.

        Args:
            token_id: The UUID primary key of the token record.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=timezone.utc))
        )
        await self._session.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for a user.

        Used by the logout-all-devices endpoint.

        Args:
            user_id: The user whose tokens should be revoked.

        Returns:
            Number of tokens that were revoked.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def delete_expired(self) -> int:
        """Hard-delete expired refresh tokens.

        Called by the Phase 2 background cleanup job.

        Returns:
            Number of records deleted.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
        result = await self._session.execute(stmt)
        return result.rowcount
