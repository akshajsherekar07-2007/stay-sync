"""User profile API endpoints.

All routes are mounted at /api/v1/users by the v1 router.

Endpoints
---------
GET   /users/me             → Return current user + profile
PATCH /users/me/profile     → Update current user's profile fields
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import MessageResponse, SuccessResponse, build_meta
from app.schemas.user import MeResponse, ProfileRead, ProfileUpdate
from app.services.user_service import UserService

router = APIRouter()


def _make_user_service(db: AsyncSession) -> UserService:
    """Instantiate UserService with required repositories."""
    return UserService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
    )


# ── GET /users/me ─────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=SuccessResponse[MeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Returns the authenticated user's account details and profile.",
)
async def get_me(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    """Return the current authenticated user with their profile."""
    service = _make_user_service(db)
    user = await service.get_me(current_user.id)

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=MeResponse.model_validate(user),
        meta=build_meta(request_id),
    )


# ── PATCH /users/me/profile ───────────────────────────────────────────────────


@router.patch(
    "/me/profile",
    response_model=SuccessResponse[ProfileRead],
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description=(
        "Partially updates the authenticated user's profile. "
        "Only provided fields are changed (PATCH semantics). "
        "Omitted fields are left unchanged."
    ),
)
async def update_my_profile(
    request: Request,
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ProfileRead]:
    """Apply partial updates to the current user's profile."""
    service = _make_user_service(db)
    profile = await service.update_profile(
        user_id=current_user.id, data=data, db=db
    )

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=ProfileRead.model_validate(profile),
        meta=build_meta(request_id),
    )
