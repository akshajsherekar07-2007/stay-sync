"""Authentication API endpoints.

All routes are mounted at /api/v1/auth by the v1 router.

Endpoints
---------
POST /auth/register       → Register new user (student or owner)
POST /auth/login          → Login, return access token + set refresh cookie
POST /auth/refresh        → Rotate refresh token, return new access token
POST /auth/logout         → Revoke current refresh token (clear cookie)
POST /auth/logout-all     → Revoke all refresh tokens for the current user
POST /auth/verify-email   → Email verification stub (Phase 1 placeholder)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.common import MessageResponse, SuccessResponse, build_meta
from app.services.auth_service import AuthService

router = APIRouter()

# Cookie name used for the HttpOnly refresh token
_REFRESH_COOKIE = "refresh_token"


def _make_auth_service(db: AsyncSession) -> AuthService:
    """Instantiate AuthService with all required repositories."""
    return AuthService(
        user_repo=UserRepository(db),
        refresh_token_repo=RefreshTokenRepository(db),
        profile_repo=ProfileRepository(db),
    )


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Write the refresh token into an HttpOnly cookie."""
    settings = get_settings()
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,  # Secure flag only in production
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh token cookie."""
    response.delete_cookie(key=_REFRESH_COOKIE, path="/")


# ── POST /auth/register ───────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=SuccessResponse[LoginResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Creates a new student or owner account. "
        "Returns an access token and sets an HttpOnly refresh token cookie."
    ),
)
async def register(
    request: Request,
    response: Response,
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[LoginResponse]:
    """Register a new user and return credentials."""
    service = _make_auth_service(db)
    _user, login_response, raw_refresh = await service.register(data=data, db=db)
    _set_refresh_cookie(response, raw_refresh)

    request_id: str = request.state.request_id if hasattr(request.state, "request_id") else ""
    return SuccessResponse(
        data=login_response,
        meta=build_meta(request_id),
    )


# ── POST /auth/login ──────────────────────────────────────────────────────────


@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Authenticates the user. Returns an access token in the response body "
        "and sets an HttpOnly refresh token cookie."
    ),
)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[LoginResponse]:
    """Authenticate and return a token pair."""
    service = _make_auth_service(db)

    # Capture device info for the refresh token record
    device_info = request.headers.get("user-agent", "")[:255]
    ip_address = request.client.host if request.client else None

    _user, login_response, raw_refresh = await service.login(
        data=data, db=db, device_info=device_info, ip_address=ip_address
    )
    _set_refresh_cookie(response, raw_refresh)

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=login_response,
        meta=build_meta(request_id),
    )


# ── POST /auth/refresh ────────────────────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=SuccessResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token",
    description=(
        "Reads the refresh token from the HttpOnly cookie, rotates it, "
        "and returns a new access token. The old cookie is replaced."
    ),
)
async def refresh_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> SuccessResponse[LoginResponse]:
    """Rotate the refresh token and return a new access token."""
    if not refresh_token_cookie:
        raise UnauthorizedException(
            message="Refresh token cookie is missing.",
            code="MISSING_REFRESH_TOKEN",
        )

    service = _make_auth_service(db)
    new_access, new_raw_refresh = await service.refresh(
        raw_token=refresh_token_cookie, db=db
    )
    _set_refresh_cookie(response, new_raw_refresh)

    settings = get_settings()
    login_response = LoginResponse(
        token={
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        user_id="",  # Omitted on refresh — client already has this
        email="",
        role="",
        full_name=None,
    )

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=login_response,
        meta=build_meta(request_id),
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────────


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout current device",
    description="Revokes the current refresh token and clears the cookie.",
)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> MessageResponse:
    """Revoke the current refresh token."""
    service = _make_auth_service(db)
    if refresh_token_cookie:
        await service.logout(raw_token=refresh_token_cookie, db=db)
    _clear_refresh_cookie(response)

    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Logged out successfully.",
        meta=build_meta(request_id),
    )


# ── POST /auth/logout-all ─────────────────────────────────────────────────────


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout all devices",
    description="Revokes all refresh tokens for the current user.",
)
async def logout_all(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    """Revoke all refresh tokens for the authenticated user."""
    service = _make_auth_service(db)
    count = await service.logout_all(user_id=current_user.id, db=db)
    _clear_refresh_cookie(response)

    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message=f"Logged out from {count} device(s) successfully.",
        meta=build_meta(request_id),
    )


# ── POST /auth/verify-email ───────────────────────────────────────────────────


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address (stub)",
    description=(
        "Phase 1 stub. Accepts a verification token but does not yet send "
        "emails or update is_email_verified. Full implementation in Phase 2."
    ),
)
async def verify_email(
    request: Request,
    token: str = "",
) -> MessageResponse:
    """Email verification placeholder for Phase 1."""
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Email verification is not yet implemented. This will be activated in Phase 2.",
        meta=build_meta(request_id),
    )
