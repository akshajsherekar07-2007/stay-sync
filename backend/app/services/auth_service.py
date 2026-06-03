"""Authentication service — registration, login, token refresh, logout.

All authentication business logic lives here.  Routers delegate to this
service and never perform DB queries directly.

Business rules enforced
-----------------------
- Duplicate email          → ConflictException(code="EMAIL_ALREADY_REGISTERED")
- Invalid credentials      → UnauthorizedException(code="INVALID_CREDENTIALS")
  (no field discrimination — intentional to prevent user enumeration)
- Inactive account         → ForbiddenException(code="ACCOUNT_DISABLED")
- Revoked/expired token    → UnauthorizedException(code="INVALID_REFRESH_TOKEN")
- is_email_verified        → NOT checked at login (Phase 1 stub — enforced in Phase 2)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, TokenResponse


class AuthService:
    """Handles registration, login, token rotation, and logout.

    Args:
        user_repo:          Repository for users table.
        refresh_token_repo: Repository for refresh_tokens table.
        profile_repo:       Repository for profiles table.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        profile_repo: ProfileRepository,
    ) -> None:
        self._user_repo = user_repo
        self._rt_repo = refresh_token_repo
        self._profile_repo = profile_repo

    # ── Registration ──────────────────────────────────────────────────────────

    async def register(
        self,
        data: RegisterRequest,
        db: AsyncSession,
    ) -> tuple[User, LoginResponse]:
        """Register a new user account and return login credentials.

        Creates a User, auto-creates a Profile with the supplied full_name,
        and issues an access token + refresh token.

        Args:
            data: Validated registration payload.
            db:   Active database session for transaction commit.

        Returns:
            A tuple of (User, LoginResponse) ready to return from the router.

        Raises:
            ConflictException: If the email is already registered.
        """
        # Guard: duplicate email
        existing = await self._user_repo.get_by_email(data.email)
        if existing is not None:
            raise ConflictException(
                message="An account with this email address already exists.",
                code="EMAIL_ALREADY_REGISTERED",
            )

        # Create user
        user = await self._user_repo.create(
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role.value,
        )

        # Auto-create profile with full_name
        await self._profile_repo.create(
            user_id=user.id,
            full_name=data.full_name,
        )

        await db.commit()
        await db.refresh(user)

        # Issue tokens
        access_token, raw_refresh = await self._issue_tokens(
            user=user, db=db, device_info=None, ip_address=None
        )

        settings = get_settings()
        login_response = LoginResponse(
            token=TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            full_name=data.full_name,
        )

        return user, login_response, raw_refresh

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(
        self,
        data: LoginRequest,
        db: AsyncSession,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, LoginResponse, str]:
        """Authenticate a user and issue a token pair.

        Args:
            data:        Validated login payload.
            db:          Active database session.
            device_info: Optional device/user-agent string.
            ip_address:  Client IP address.

        Returns:
            Tuple of (User, LoginResponse, raw_refresh_token).

        Raises:
            UnauthorizedException: If credentials are invalid.
            ForbiddenException:    If the account is disabled.
        """
        # Fetch user — intentionally same error for missing vs wrong password
        user = await self._user_repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException(
                message="Invalid email or password.",
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise ForbiddenException(
                message="This account has been disabled. Contact support.",
                code="ACCOUNT_DISABLED",
            )

        # Update last login
        await self._user_repo.update_last_login(user.id)

        # Issue tokens
        access_token, raw_refresh = await self._issue_tokens(
            user=user, db=db, device_info=device_info, ip_address=ip_address
        )

        await db.commit()

        # Load profile name for response
        profile = await self._profile_repo.get_by_user_id(user.id)
        full_name = profile.full_name if profile else None

        settings = get_settings()
        login_response = LoginResponse(
            token=TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            full_name=full_name,
        )

        return user, login_response, raw_refresh

    # ── Token refresh ─────────────────────────────────────────────────────────

    async def refresh(
        self,
        raw_token: str,
        db: AsyncSession,
    ) -> tuple[str, str]:
        """Rotate a refresh token and issue a new access + refresh pair.

        The old refresh token is revoked atomically before the new pair is issued.

        Args:
            raw_token: The raw refresh token from the cookie.
            db:        Active database session.

        Returns:
            Tuple of (new_access_token, new_raw_refresh_token).

        Raises:
            UnauthorizedException: If the token is invalid, expired, or revoked.
        """
        token_hash = hash_token(raw_token)
        record = await self._rt_repo.get_by_hash(token_hash)

        if record is None or not record.is_valid:
            raise UnauthorizedException(
                message="Refresh token is invalid or has expired.",
                code="INVALID_REFRESH_TOKEN",
            )

        # Load user
        user = await self._user_repo.get(record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException(
                message="Refresh token is invalid or has expired.",
                code="INVALID_REFRESH_TOKEN",
            )

        # Revoke old token
        await self._rt_repo.revoke_token(record.id)

        # Issue new pair
        new_access, new_raw_refresh = await self._issue_tokens(
            user=user,
            db=db,
            device_info=record.device_info,
            ip_address=record.ip_address,
        )

        await db.commit()
        return new_access, new_raw_refresh

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, raw_token: str, db: AsyncSession) -> None:
        """Revoke a single refresh token (logout current device).

        Args:
            raw_token: The raw refresh token from the cookie.
            db:        Active database session.
        """
        token_hash = hash_token(raw_token)
        record = await self._rt_repo.get_by_hash(token_hash)
        if record is not None:
            await self._rt_repo.revoke_token(record.id)
            await db.commit()

    async def logout_all(self, user_id: uuid.UUID, db: AsyncSession) -> int:
        """Revoke all refresh tokens for a user (logout all devices).

        Args:
            user_id: The user whose tokens should all be revoked.
            db:      Active database session.

        Returns:
            Number of tokens that were revoked.
        """
        count = await self._rt_repo.revoke_all_for_user(user_id)
        await db.commit()
        return count

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _issue_tokens(
        self,
        user: User,
        db: AsyncSession,
        device_info: str | None,
        ip_address: str | None,
    ) -> tuple[str, str]:
        """Create and persist a refresh token; sign and return an access token.

        Args:
            user:        The authenticated user.
            db:          Active session (flush happens here, commit by caller).
            device_info: Optional device string.
            ip_address:  Client IP.

        Returns:
            Tuple of (access_token_str, raw_refresh_token_str).
        """
        settings = get_settings()
        raw_refresh, refresh_hash = create_refresh_token()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self._rt_repo.create_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )

        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        return access_token, raw_refresh
