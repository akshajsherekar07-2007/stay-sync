"""Pydantic schemas package."""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import (
    ComponentHealth,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationInfo,
    ResponseMeta,
    SuccessResponse,
    build_meta,
)
from app.schemas.user import (
    MeResponse,
    ProfileRead,
    ProfileUpdate,
    UserRead,
)

__all__ = [
    # common
    "ComponentHealth",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "ResponseMeta",
    "SuccessResponse",
    "build_meta",
    # auth
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "TokenResponse",
    # user
    "MeResponse",
    "ProfileRead",
    "ProfileUpdate",
    "UserRead",
]

