"""User service — profile management business logic.

Handles get-me and profile update operations.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.profile import Profile
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ProfileUpdate


class UserService:
    """Handles user profile read and update operations.

    Args:
        user_repo:    Repository for users table.
        profile_repo: Repository for profiles table.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        profile_repo: ProfileRepository,
    ) -> None:
        self._user_repo = user_repo
        self._profile_repo = profile_repo

    async def get_me(self, user_id: uuid.UUID) -> User:
        """Load the current user with their profile eagerly joined.

        Args:
            user_id: The authenticated user's UUID.

        Returns:
            ``User`` ORM instance with ``.profile`` populated.

        Raises:
            NotFoundException: If the user no longer exists (edge case).
        """
        user = await self._user_repo.get_with_profile(user_id)
        if user is None:
            raise NotFoundException(
                message="User not found.",
                code="USER_NOT_FOUND",
            )
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        data: ProfileUpdate,
        db: AsyncSession,
    ) -> Profile:
        """Apply a partial update to the user's profile (PATCH semantics).

        Only fields explicitly provided (non-None) are updated.  If no profile
        exists yet (e.g. owner who skipped profile creation) a new one is created.

        Args:
            user_id: The authenticated user's UUID.
            data:    Validated PATCH payload.
            db:      Active database session.

        Returns:
            The updated (or newly created) ``Profile`` instance.
        """
        # Only pass non-None fields
        update_kwargs = data.model_dump(exclude_none=True)

        profile = await self._profile_repo.upsert(
            user_id=user_id,
            **update_kwargs,
        )
        await db.commit()
        await db.refresh(profile)
        return profile
