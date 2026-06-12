"""Pydantic schema (DTO) package for StaySync API.

All request/response schemas are organized by domain module.
Import from here for a flat namespace::

    from app.schemas import RegisterRequest, PropertyCreate, BedRead
"""

# Phase 1.4
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import MeResponse, ProfileRead, ProfileUpdate

# Phase 1.5
from app.schemas.property import (
    PropertyCreate,
    PropertyFilter,
    PropertyListItem,
    PropertyRead,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.schemas.floor import FloorCreate, FloorRead, FloorUpdate
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.schemas.bed import BedCreate, BedRead, BedUpdate
from app.schemas.amenity import AmenityAttach, AmenityRead
from app.schemas.image import ImageRead, ImageReorder, ImageUpdate

# Common
from app.schemas.common import (
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    SuccessResponse,
    build_meta,
)
