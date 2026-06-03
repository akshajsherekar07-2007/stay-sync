"""Authentication and authorization FastAPI dependency functions.

Provides injectable dependencies for:
- Extracting and validating the Bearer token from the Authorization header.
- Loading the current user from the database.
- Role-based access control (RBAC) guards.

Usage
-----
.. code-block:: python

    from app.dependencies.auth import get_current_user, require_owner

    @router.post("/properties")
    async def create_property(
        current_user: User = Depends(require_owner),
        db: AsyncSession = Depends(get_db),
    ) -> ...:
        ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# HTTPBearer will return 403 by default if no credential header is present.
# We use auto_error=False so we can return a consistent 401 instead.
_http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_http_bearer),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract the Bearer token, validate it, and return the authenticated user.

    Dependency chain:
        HTTP Authorization header → decode JWT → load User from DB.

    Args:
        credentials: Injected by FastAPI's HTTPBearer scheme.
        db:          Active database session.

    Returns:
        The authenticated ``User`` ORM instance.

    Raises:
        UnauthorizedException (401): Token missing, invalid, or expired.
        ForbiddenException    (403): Account is inactive.
    """
    if credentials is None:
        raise UnauthorizedException(
            message="Authentication required. Provide a Bearer token.",
            code="MISSING_TOKEN",
        )

    payload = decode_access_token(credentials.credentials)

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(
            message="Invalid token payload.",
            code="INVALID_TOKEN",
        )

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise UnauthorizedException(
            message="Invalid token payload.",
            code="INVALID_TOKEN",
        ) from exc

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if user is None:
        raise UnauthorizedException(
            message="User account not found.",
            code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise ForbiddenException(
            message="This account has been disabled. Contact support.",
            code="ACCOUNT_DISABLED",
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_http_bearer),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Like ``get_current_user`` but returns None instead of raising when no token.

    Used on public endpoints that return richer data for authenticated users.

    Returns:
        The authenticated ``User`` or ``None`` if no token was supplied.
    """
    if credentials is None:
        return None
    return await get_current_user(credentials=credentials, db=db)


def require_role(*roles: UserRole):
    """Factory that returns a dependency raising 403 if the user's role is not allowed.

    Args:
        *roles: One or more ``UserRole`` values that are permitted.

    Returns:
        A FastAPI dependency function.

    Usage:
        .. code-block:: python

            @router.delete("/{id}")
            async def delete(current_user = Depends(require_role(UserRole.OWNER))):
                ...
    """
    allowed = set(roles)

    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if UserRole(current_user.role) not in allowed:
            raise ForbiddenException(
                message="You do not have permission to perform this action.",
                code="FORBIDDEN",
                details={"required_roles": [r.value for r in allowed]},
            )
        return current_user

    return _check_role


# ── Convenience shorthand dependencies ────────────────────────────────────────

def require_owner(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the current user to be an OWNER or ADMIN.

    Raises:
        ForbiddenException (403): If the user is a student.
    """
    if UserRole(current_user.role) not in (UserRole.OWNER, UserRole.ADMIN):
        raise ForbiddenException(
            message="Only property owners can perform this action.",
            code="OWNER_REQUIRED",
        )
    return current_user


def require_student(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the current user to be a STUDENT or ADMIN.

    Raises:
        ForbiddenException (403): If the user is an owner.
    """
    if UserRole(current_user.role) not in (UserRole.STUDENT, UserRole.ADMIN):
        raise ForbiddenException(
            message="Only students can perform this action.",
            code="STUDENT_REQUIRED",
        )
    return current_user
